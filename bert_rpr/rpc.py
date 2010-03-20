# -*- coding: latin-1 -*-

##
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
##
##The views and conclusions contained in the software and documentation are those of the
##authors and should not be interpreted as representing official policies, either expressed
##or implied, of Roger Wenham.


ID = "$Id: bert_rpc.py 260 2010-03-20 06:44:22Z Roger $"
VER = "$Revision: 260 $"

# Classes encapsulating BERT-RPC
#
# BertRpcServer
# -------------
# Inherit from the BertRpcServer class when creating a BERT-RPC server. The class
# will do all the necessary work registering with a Remote Procedure Registry if
# necessary.
#
# BertRpcClient
# -------------
# Inherit from the BertRpcClient class when creating a BERT-RPC client. The class
# will do all the necessary work locating the BERT-RPR and resolving the remote
# procedure.

import select, types, time, struct, sys, traceback
from ConfigParser import ConfigParser as CfgParser
from socket import *
import bert
import rpc
import finder
#import config

class TransferError(Exception):
    pass

class ProtocolError(Exception):
    pass

class ServerError(Exception):
    pass

defaultConf = {
    'default_tcp_port': 48490,
    'def_srv_port': 48493
    }
#
class BertRpcServer(object):
    def __init__(self, modules, srvAddrs=[], **kwargs):
        '''
        modules is a dictionary containing the modules tp beserved, a module may
        be either a python module or an object. The module function or object
        method to be served must have an exposed attribute set to True.
            modules = {
                'mod1': mod1,
                ...
                'modn': modn,
                }
        If modules is None, then BertRpcServer has been used as a base class and
        the class name of the inheriting class is used as the mofule name and
        all class methods marked exposed are served.
        srcAddrs is a list of hostname port tuples used to specify the hostname
        and ports to listen on. There will normally be only one tuple unless
        the server is multi homed.
            srvAddrs = [(<hostname>, <port number>), ...]
        if srvAddrs is not supplied or is an empty list, the degault port will
        be used to server on.
        '''
        # Set this flag true to terminate the server cleanly
        self.terminate = False
        self.verbose = kwargs.get('verbose', False)

        # Modules to serve
        if modules is None:
            self.modules = {self.__class__.__name__: self }
        else:
            self.modules = modules

        # Get the configuration
        self.cfg = defaultConf
        #self.cfg.update(config.config)

        # Set up the listen addresses
        if len(srvAddrs) == 0:
            # None given so serve on the default port
            self.srvAddrs = [(getfqdn(), self.cfg['def_srv_port'])]
        else:
            self.srvAddrs = srvAddrs

        # Open the sockets for listening
        self.socks = self._open()

    def _open(self):
        '''Open the socket(s) for serving'''
        socks = []
        for addr in self.srvAddrs:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            sock.bind(addr)
            sock.listen(5)
            socks.append(sock)
        return socks

    def serve(self):
        '''Serve any incoming requests, until the terminate flag is set'''
        while not self.terminate:
            i,o,e = select.select(self.socks, [], [], 5)
            for sock in i:
                try:
                    sock, addr = sock.accept()
                    self._handleConnection(sock, addr)
                except error,e:
                    if len(args) > 0 and e.args[0] == EMFILE:
                        # Too many open sockets! Gi
                        sleep(1)
                        continue
                    raise
                except Exception, e:
                    sock.close()
                    raise
        if self.verbose: print "\tServer Terminated"

    def _handleConnection(self, sock, addr):
        '''Handle the incoming connecton'''
        _, module, func, args = self._decodeMessage(self._getMessage(sock))
        args = tuple(args)

        #message is {call, Module, Function, Arguments}
        try:
            # Check that the call target exists
            if not self.modules.has_key(module):
                raise AttributeError, "No such module: %s" % (module)

            fnName = 'rpc_%s' % (func)
            if not hasattr(self.modules[module], fnName):
                raise AttributeError, "No such function exposed: %s" % (func)

            # Get the target code object
            fun = getattr(self.modules[module], fnName, None)

            # Do the call
            rep = fun(*args)

            # Return the result
            reply = self._encodeMessage((bert.Atom('reply'), rep))
        except:
            # An exception happened, so return the traceback
            reply = self._encodeMessage(self._makeExceptionMessage('server', 2, sys.exc_info()))

        self._sendMessage(sock, reply)

    def _getMessage(self, sock):
        '''Receive the BERP message from the socket'''
        self._waitForData(sock, 2)

        # Receive the message size
        size = sock.recv(4)
        if len(size) != 4:
            return None
        size = int(struct.unpack("!L",size)[0])

        # then the message body
        message = ''
        rsize = size
        while rsize > 0:
            sock = self._waitForData(sock, 2)
            data = sock.recv(rsize)
            rsize -= len(data)
            message  += data

        return message

    def _waitForData(self, sock, tout=5):
        '''Wait for data to arrive at the socket, for a max fo tout seconds'''
        i = select.select([sock], [], [], tout)[0]
        if len(i) > 0:
            return i[0]

        # An empty list is returned if the select times out
        raise TransferError, "Waited for longer than %s secs" % (tout)

    def _sendMessage(self, sock, msg):
        '''Send the reply back to the client'''
        try:
            while len(msg) > 0:
                cs = sock.send(msg)
                msg = msg[cs:]
        except:
            if self.verbose: print("Exception: Socket send data failed (%s)." % (msg))
            raise

    def _decodeMessage(self, message):
        ''' Decode a bert message'''
        return bert.decode(message)

    def _encodeMessage(self, message):
        '''Encode a bert message, pre-pending the 4 size bytes'''
        bmsg = bert.encode(message)
        size = struct.pack("!L",len(bmsg))
        return ''.join([size, bmsg])

    def _makeExceptionMessage(self, Type, Code, exc_info):
        '''
        create an error message containing a python traceback

        {error, {Type, Code, Class, Detail, Backtrace}}

        {error, {server, 2,
            <<"BERTError">>,
            <<"function 'img_size' not found on module 'photox'">>,
            [<<"file:line:context">>]}}

        Valid error types are protocol, server, user, and proxy. Codes 0-99 are
        reserved as predefined error messages. Codes 100+ are for custom use.

        Protocol Error Codes
            0 = Undesignated
            1 = Unable to read header
            2 = Unable to read data

        Server Error Codes
            0 = Undesignated
            1 = No such module
            2 = No such function
        '''
        exceptionType, exceptionValue, exceptionTraceback = exc_info
        tb = traceback.extract_tb(exceptionTraceback)
        return (bert.Atom('error'), (bert.Atom(Type), Code, exceptionType.__name__, str(exceptionValue), tb))


class BertRpcClient(object):
    def __init__(self, server=None, timeout=5):
        '''
        Inherit from the BertRpcClient class when creating a BERT-RPC client.
        '''
        # The configuration
        self.cfg = defaultConf
        #self.cfg.update(config.config)

        # Set up the server addresses
        if server is None:
            self.serverAddr = self.cfg.get('def_srv_addr')
        else:
            self.serverAddr = server

        self.Socket  = None
        self.timeout = timeout

    def call(self, module, func, *args):
        '''Call the remote function'''

        # Open the connection
        self._open()

        # Send the BERT call message
        ret = self.send((bert.Atom('call'), module, func, args))

        # Deal with the reply
        if len(ret) > 1 and ret[0] == 'reply':
            # All is OK
            return ret[1]
        elif len(ret) > 1 and ret[0] == 'error':
            # If we got an error, reraise the exception
            self._raiseException(ret[1])
        else:
            raise InvalidResponse, "Bert Message = %s" % (ret)

    def cast(self, module, func, *args):
        '''Cast to the remote function'''

        # Open the connection
        self._open()

        # Send the BERT cast message
        ret = self.send((bert.Atom('cast'), module, func, args))

        # Deal with the reply
        if len(ret) > 1 and ret[0] == 'noreply':
            return
        elif len(ret) > 1 and ret[0] == 'error':
            self._raiseException(ret[1])
        else:
            raise InvalidResponse, "Bert Message = %s" % (ret)

    def _open(self):
        '''Open a connection to the server'''
        # If the connection is already open....
        if self.Socket != None:
            return self.Socket

        # Create a socket
        try:
            self.Socket = socket(AF_INET, SOCK_STREAM)
            self.Socket.setsockopt(SOL_SOCKET,SO_KEEPALIVE,1)
        except Exception, e:
            if self.verbose: print "Opened failed", str(e)
            raise

        # Connect the socket
        try:
            self.Socket.connect(self.serverAddr)
        except:
            raise

        return self.Socket

    def send(self, msg):
        '''Send the BERP message to the socket'''
        if msg is None:
            if self.verbose: print("Error: Trying to send None message!")
            return None

        # Encode the message
        bmsg = self._encodeMessage(msg)

        # Send the message
        try:
            while len(bmsg) > 0:
                cs = self.Socket.send(bmsg)
                bmsg = bmsg[cs:]
        except:
            if self.verbose: print("Exception: Socket send data failed (%s)." % (bmsg))
            self._close()
            raise

        # Get the reply size and body
        try:
            data = self.Socket.recv(4)
            if len(data) == 4:
                size = int(struct.unpack("!L",data)[0])
        except:
            self._close()
            raise

        # Get the body of the reply
        try:
            data = ''
            while len(data) < size:
                data = data + self.Socket.recv(size - len(data))
        except:
            self._close()
            raise InternalError, "Failed to receive reply"

        # decode and return the reply
        return self._decodeMessage(data)

    def _close(self):
        '''Tidily close the socket'''
        if self.Socket:
            try:
                self.Socket.shutdown(2)
                self.Socket.close()
                if self.verbose: print("Socket closed.")
            except:
                if self.verbose: print("Exception: Socket close failed.")

        self.Socket = None

    def _decodeMessage(self, message):
        ''' Decode a bert message'''
        return bert.decode(message)

    def _encodeMessage(self, message):
        '''Encode a bert message, pre-pending the 4 size bytes'''
        bmsg = bert.encode(message)
        size = struct.pack("!L",len(bmsg))
        return ''.join([size, bmsg])

    def _raiseException(self, exc):
        '''Raise an exception corresponding to the BERT-RPC codes'''
        Type, Code, exceptionType, exceptionValue, tb = exc
        if Type == 'protocol':
            raise ProtocolError(Code, exceptionType, exceptionValue, tb)
        elif Type == 'server':
            raise ServerError(Code, exceptionType, exceptionValue, tb)
        else:
            raise AttributeError, "Unknown error format: %s" % (str(exc))


