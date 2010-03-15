# -*- coding: latin-1 -*-

'''
Copyright 2010 Roger Wenham. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY Roger Wenham ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Roger Wenham OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of Roger Wenham.
'''

ID = "$Id: bert_rpr.py 255 2010-03-14 08:33:19Z Roger $"
VER = "$Revision: 255 $"

# The BERT Remote Procedure Registry

import socket, threading, getopt, sys, select
import bert
import bert_rpc

DEFAULT_PORT = 48490
DEFAULT_BROADCAST_PORT = 48491

class Registry(bert_rpc.BertRpcServer):
    '''
    BERT_RPC registry
    '''
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', DEFAULT_PORT)
        self.verbose = kwargs.get('verbose', False)

        # Initialise the base class with modules = None so that the class
        # instance is server with the module name = class name.
        bert_rpc.BertRpcServer.__init__(self, None, [('', self.port)], verbose=self.verbose)

        self.registry = {}

        self.sock = None

    def rpc_ping(self):
        return ('reply', True)

    def rpc_terminate(self):
        self.terminate = True
        return ('reply', True)

    def rpc_verbose(self, verbose=True):
        self.verbose = verbose
        return ('reply', True)

    def rpc_register(self, module, function, meta, host, port):
        place = (host, port)
        if not self.registry.has_key(module):
            self.registry[module] = {}
        if not self.registry[module].has_key(function):
            self.registry[module][function] = {}
        if not self.registry[module][function].has_key(place):
            self.registry[module][function][place] = meta
        return ('reply', True)

    def rpc_register_many(self, functions):
        for function in functions:
            module, function, meta, host, port = function
            self.rpc_register(module, function, meta, host, port)
        return ('reply', True)

    def rpc_resolve(self, module, function):
        if self.registry.has_key(module):
            if self.registry[module].has_key(function):
                return ('reply', self.registry[module][function].keys())
        return ('reply', [])

    def rpc_get_modules(self):
        return ('reply', self.registry.keys())

    def rpc_get_functions(self, module):
        if self.registry.has_key(module):
            return ('reply', self.registry[module].keys())
        return ('reply', [])

    def rpc_get_metadata(self, module=None, function=None):
        meta = []
        if module is None:
            for module in self.registry.keys():
                for function in self.registry[module].keys():
                    for place in self.registry[module][function].keys():
                        meta.append("%s.%s.%s.%s: %s" % (place[0], place[1], module, function, self.registry[module][function][place]))
        elif function is None and self.registry.has_key(module):
            for function in self.registry[module].keys():
                for place in self.registry[module][function].keys():
                    meta.append("%s.%s.%s.%s: %s" % (place[0], place[1], module, function, self.registry[module][function][place]))
        elif self.registry.has_key(module) and self.registry[module].has_key(function):
            for place in self.registry[module][function].keys():
                meta.append("%s.%s.%s.%s: %s" % (place[0], place[1], module, function, self.registry[module][function][place]))

        return ('reply', meta)

    def dump(self, module=None, function=None):
        if module is None and function is None:
            return ('reply', self.registry)
        elif function is None and self.registry.has_key(module):
            return ('reply', self.registry[module])
        else:
            return ('reply', self.registry[module][function])

        return ('reply', [])

    def rpc_deregister_module(self, module, host, port):
        place = (host, port)
        if self.registry.has_key(module):
            for function in self.registry[module].keys():
                del self.registry[module][function][place]

        return ('reply', True)

    def rpc_deregister_function(self, module, function, host, port):
        place = (host, port)
        if self.registry.has_key(module):
            del self.registry[module][function][place]

        return ('reply', True)

class BroadcastListner(threading.Thread):
    ''' Listen for broadcasts '''
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        self.port = kwargs.get('port', DEFAULT_PORT)
        self.bcport = kwargs.get('bcport', DEFAULT_BROADCAST_PORT)
        self.verbose = kwargs.get('verbose', False)
        self.terminate = False

    def run(self):
        bc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bc_socket.bind(('',self.bcport))

        while not self.terminate:
            i,o,r = select.select([bc_socket], [], [], 1)
            for sock in i:
                message , address = sock.recvfrom(8192)
                if self.verbose: print "\tReceived broadcast from %s" % (str(address))

                msg = bert.decode(message)
                #print "msg= %s" % (str(msg))

                msg = bert.encode(('reply', (socket.getfqdn(), self.port)))

                try:
                    sock.sendto(msg, address)
                except:
                    pass



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
            port = int(a)
        elif o in ("-b", "--bcport"):
            bcport = int(a)
        else:
            usage("Unknown option %s" % (o))

    if verbose: print "\tStarting BERT RPC Registry"
    bc = BroadcastListner(port=port, bcport=bcport, verbose=verbose)
    bc.start()
    if verbose: print "\tListening for broadcasts on port: %s" % (bcport)
    reg = Registry(*args, verbose = verbose, port=port)
    if verbose: print "\tServing on port: %s" % (port)
    while not reg.terminate:
        reg.serve()
    bc.terminate = True
    if verbose: print "\tBERT RPC Registry Exited"

if __name__ == "__main__":
    main()

