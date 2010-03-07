# -*- coding: latin-1 -*-

ID = "$Id:$"
VER = "$Revision:$"

# The BERT Remote Procedure Registry

import socket, threading, getopt, sys
import bert
import bert_server

DEFAULT_PORT = 48490
DEFAULT_BROADCAST_PORT = 48491


class BroadcastResponder(threading.Thread):
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        self.port = kwargs.get('port', DEFAULT_PORT)
        self.bcport = kwargs.get('bcport', DEFAULT_BROADCAST_PORT)
        self.verbose = kwargs.get('verbose', False)

    def run(self):
        bc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bc_socket.bind(('',self.bcport))

        if self.verbose: print "BroadcastResponder: Waiting for broadcasts on %s: %s" % ('',self.bcport)
        while True :
            message , address = bc_socket.recvfrom(8192)
            if self.verbose: print "Received broadcast from %s" % (str(address))

            msg = bert.decode(message)
            print "msg= %s" % (str(msg))

            msg = bert.encode(('reply', (socket.getfqdn(), self.port)))

            try:
                bc_socket.sendto(msg, address)
            except:
                pass

class BertRpLocationService(bert_rpc.BertRpcServer):
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', DEFAULT_PORT)
        bert_server.BertServer.__init__(self, [('', self.port)])
        self.sock = None
        self.funs = {
            'rpfinder': {
                'ping': self.ping
                }
            }

    def ping(self):
        return ('reply', 'OK')



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

    bc = BroadcastResponder(port=port, bcport=bcport, verbose=verbose).start()
    rpf = BertRpLocationService(*args, verbose = verbose, port=port, bcport=bcport)
    rpf.serve()
    rpf.serve()
    rpf.serve()
    rpf.serve()
    rpf.serve()
    rpf.serve()
    print "exit"

if __name__ == "__main__":
    main()

