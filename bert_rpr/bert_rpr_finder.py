# -*- coding: latin-1 -*-

ID = "$Id:$"
VER = "$Revision:$"

# Bert Remote Procesure Registry Finder

import sys, socket, getopt
import bert, bert_server

DEFAULT_PORT = 48490
DEFAULT_BROADCAST_PORT = 48491

class BertRpFinder(object):
    def __init__(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        self.port = kwargs.get('port', DEFAULT_PORT)
        self.bport = kwargs.get('bport', DEFAULT_BROADCAST_PORT)
        self.places = []

        for arg in args:
            if not isinstance(arg, str):
                raise AttributeError, "Illegal argument: %s must be a string" % (arg)
            arg = arg.strip()
            if not ':' in arg:
                self.places.append((arg, self.port))
            else:
                host, port = arg.split(':')
                try:
                    port = int(port)
                    self.places.append((host, port))
                except:
                    raise AttrError, "Illegal argument: port must be an integer: %s" % (port)

        self.rpRegistries = []

    # Find an RpFinder
    def find(self, verbose=False):
        if self.verbose: print "Find an RpFinder"
        if not self.verbose and verbose: self.verbose=verbose

        # First try the local machine.
        if self.verbose: print "Trying the local machine"
        if self.search((socket.getfqdn(), self.port)):
            if self.verbose: print "RPF located"
            return True

        # First try the supplied places (if any)
        if self.verbose and self.places: print "Trying places"
        elif self.verbose and not self.places: print "No places supplied"
        for place in self.places:
            if self.verbose: print "Trying %s" % (str(place))
            if self.search(place):
                if self.verbose: print "RPF located"
                return True

        # Next broadcast for places
        if self.verbose: print "Broadcasting..."
        for place in self.broadcastForPlaces():
            if self.verbose: print "Trying %s" % (str(place))
            if self.search(place):
                if self.verbose: print "RPF located"
                return True

        print "No RPF's found"

        return False

    # Broadcast for RpFinders
    def broadcastForPlaces(self):
        places = []
        my_addr = socket.getfqdn()
        bc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bc_socket.settimeout(5)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

        if self.verbose: print "Broadcasting on %s:%s" % ('<broadcast>' ,self.bport)
        bc_socket.sendto(bert.encode(my_addr), ('<broadcast>' ,self.bport))

        while True:
            try:
                message , address = bc_socket.recvfrom(8192)
            except socket.timeout, e:
                if self.verbose:
                    if places: print "No more replies to the broadcast"
                    else: print "No replies to the broadcast"
                break

            msg = bert.decode(message)
            if self.verbose: print "Reply=%s from=%s"% (msg, address)

            try:
                if not msg[1] in places:
                    places.append(msg[1])
            except Exception, e:
                if self.verbose: print "Error decoding broadcast reply: %s" % (str(e))

            bc_socket.settimeout(1)

        bc_socket.close()
        return places

    # Try the supplied location.
    # If an RpFinder is found, put it in the list and return True
    # else return False
    def search(self, place):
        'Try to contact a RpFinder at the given address'
        if self.verbose: print "Checking RpFinder at: %s" % (str(place))
        try:
            if self.ping(place):
                self.rpRegistries.append(place)
                return True
        except:
            raise
        return False


    def ping(self, place):
        print "PING"
        reply = bert_server.BertClient(place).send(('call', 'rpfinder', 'ping', []))
        print "ping", reply
        if len(reply) > 1 and reply[1] == 'OK':
            return True
        return False

def usage(msg = None):
    if msg:
        print msg
    print """
python bert_rprfinder [-v][-h] [host[:port] ... ]
    <place>     A list of one or more places to look
                hostname will try the given host on the default port.
                hostname:port will try the given host on the given port.
                :port will try the local host on the given port.
    -p port     Will use the given port as the default port.
    -b port     Will use the given port as the default port for broadcasts.
    -v          Verbose
    -h          Print this message
"""
    sys.exit(1)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "b:p:vhv", ["bcport=", "port=", "verbose", "help"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    port = 48490
    bcport = 48491
    verbose = False
    for o, a in opts:
        if o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-p", "--port"):
            port = a
        elif o in ("-b", "--bcport"):
            bcport = a
        else:
            usage("Unknown option %s" % (o))

    rpf = BertRpFinder(*args, verbose = verbose, port=port, bcport=bcport).find(verbose)

if __name__ == "__main__":
    main()
