# -*- coding: latin-1 -*-

##Copyright 2010 Roger Wenham. All rights reserved.
##
##Redistribution and use in source and binary forms, with or without modification, are
##permitted provided that the following conditions are met:
##
##   1. Redistributions of source code must retain the above copyright notice, this list of
##      conditions and the following disclaimer.
##
##   2. Redistributions in binary form must reproduce the above copyright notice, this list
##      of conditions and the following disclaimer in the documentation and/or other materials
##      provided with the distribution.
##
##THIS SOFTWARE IS PROVIDED BY Roger Wenham ``AS IS'' AND ANY EXPRESS OR IMPLIED
##WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
##FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Roger Wenham OR
##CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
##CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
##SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
##ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
##NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
##ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
This module contains the necessary code to locate a BERT Remote Procedure Registry
'''

ID = "$Id: bert_rpr_finder.py 260 2010-03-20 06:44:22Z Roger $"
VER = "$Revision: 260 $"

# Bert Remote Procesure Registry Finder

import sys, socket, getopt
import bert, rpc

DEFAULT_PORT = 48490
DEFAULT_BROADCAST_PORT = 48491

class BertRprFinder(object):
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

        self.Registries = []

    # Find an RpFinder
    def find(self, all=False):
        '''
        If the sll parameter is True, then all methods will be tries and a
        list of all RPR's found will be returned.
        '''
        if self.verbose: print "\tSearching for a BERT-Remote Procedure Repository"

        # First try the local machine.
        if self.verbose: print "\tTrying the local machine"
        if self.search((socket.getfqdn(), self.port)):
            if self.verbose: print "\tRPR located: %s:%s" % (socket.getfqdn(), self.port)
            if not all: return self.Registries

        # First try the supplied places (if any)
        if self.verbose and self.places: print "\tTrying supplied places",
        elif self.verbose and not self.places: print "\tNo places supplied"
        for place in self.places:
            if self.verbose: print "\tTrying %s" % (str(place))
            if self.search(place):
                if self.verbose: print "\tRPR located: %s:%s" % place
                if not all: return self.Registries

        # Next broadcast for places
        if self.verbose: print "\tBroadcasting for an RPR"
        for place in self.broadcastForPlaces():
            if self.verbose: print "\tResponse from %s:%s" % place
            if self.search(place):
                if self.verbose: print "\tRPR located: %s:%s" % place
                if not all: return self.Registries

        if self.verbose: print "\t%s RPR's found" % (len(self.Registries))
        return self.Registries

    # Broadcast for RpFinders
    def broadcastForPlaces(self):
        places = []
        my_addr = socket.getfqdn()
        bc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bc_socket.settimeout(5)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)

        if self.verbose: print "\tBroadcasting for an RPR on %s:%s" % ('<broadcast>' ,self.bport)
        bc_socket.sendto(bert.encode(my_addr), ('<broadcast>' ,self.bport))

        while True:
            try:
                message , address = bc_socket.recvfrom(8192)
            except socket.timeout, e:
                if self.verbose:
                    if places: print "\tNo more replies to the broadcast"
                    else: print "\tNo replies to the broadcast"
                break

            msg = bert.decode(message)
            if self.verbose: print "\tReply=%s from=%s"% (msg, address)

            try:
                if not msg[1] in places:
                    places.append(msg[1])
            except Exception, e:
                if self.verbose: print "\tError decoding broadcast reply: %s" % (str(e))

            bc_socket.settimeout(1)

        bc_socket.close()
        return places

    # Try the supplied location.
    # If an RpFinder is found, put it in the list and return True
    # else return False
    def search(self, place):
        'Try to contact a RpFinder at the given address'
        try:
            if self.ping(place):
                self.Registries.append(place)
                return True
        except:
            raise
        return False

    def ping(self, place):
        try:
            reply = rpc.BertRpcClient(place).call('Registry', 'ping')
        except socket.error, e:
            return False

        if len(reply) > 1 and reply[1] == True:
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

    rpf = BertRprFinder(*args, verbose = verbose, port=port, bcport=bcport).find(verbose)

if __name__ == "__main__":
    main()

