# -*- coding: latin-1 -*-

ID = "$Id:$"
VER = "$Revision:$"

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

import select, types, time, struct, ConfigParser
from ConfigParser import ConfigParser as CfgParser
from socket import *
import bert
import config

class TransferError(Exception):
    pass

class ConnectionError(Exception):
    pass

class BertError(Exception):
    pass

defaultConf = {
    'default_tcp_port': 48490,
    'def_srv_addr': (getfqdn(), 48493)
    }
#
class BertRpcServer(object):
    def __init__(self, modules, srvAddrs=[]):
        '''
        srcAddrs is a list of hostname port tuples used to specify the hostname
        and ports to listen on for multi homed hosts.
        '''
        # Set this flag true to terminate the server
        self.terminate = False

        # Modules to serve
        self.modules = modules

        # Get the configuration
        self.cfg = defaultConf
        self.cfg.update(config.config)

        # Set up the listen addresses
        if len(srvAddrs) == 0:
            self.srvAddrs = [self.cfg.get('def_srv_addr')]
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
        '''Serve for timeout seconds'''
        # if timeout is 0, the server until terminate is set, else return after
        # timeout secs or the first serve.
        while not self.terminate:
            i,o,e = select.select(self.socks, [], [], 5)
            for sock in i:
                try:
                    sock, addr = sock.accept()
                    # Do this in a new thread
                    self._handleConnection(sock, addr)
                except error,e:
                    if len(args) > 0 and e.args[0] == EMFILE:
                        # Too many open sockets! Gi
                        sleep(1)
                        continue
                    raise
                except Exception, e:
                    print "Exception: %s" % (str(e))
                    sock.close()
                    raise

    def _handleConnection(self, sock, addr):
        '''Handle th incoming connecton'''
        message = self._getMessage(sock)
        call = self._decodeMessage(message)
        #{call, Module, Function, Arguments}
        _, module, func, args = call
        print "call", module, func, args
        rep = self.modules[module][func](*args)
        reply = self._encodeMessage(('reply', rep))
        self._sendMessage(sock, reply)

    def _getMessage(self, sock):
        '''Receive the BERP message from the socket'''
        self._waitForData(sock, 5)
        size = sock.recv(4)
        if len(size) != 4:
            return None
        size = int(struct.unpack("!L",size)[0])
        message = ''
        rsize = size
        while rsize > 0:
            sock = self._waitForData(sock, 5)
            data = sock.recv(rsize)
            rsize -= len(data)
            message  += data
        return message

    def _waitForData(self, sock, tout=5):
        '''Wait for data to arrive at the socket'''
        i = select.select([sock], [], [], tout)[0]
        if len(i) > 0:
            return i[0]
        raise TransferError, "Waited for longer than %s secs" % (tout)

    def _sendMessage(self, sock, msg):
        try:
            while len(msg) > 0:
                cs = sock.send(msg)
                msg = msg[cs:]
        except:
            print("Exception: Socket send data failed (%s)." % (msg))
            raise

    def _decodeMessage(self, message):
        return bert.decode(message)

    def _encodeMessage(self, message):
        bmsg = bert.encode(message)
        size = struct.pack("!L",len(bmsg))
        return ''.join([size, bmsg])


class BertRpcClient(object):
    def __init__(self, server=None, timeout=5):
        # The configuration
        self.cfg = defaultConf
        self.cfg.update(config.config)

        # Set up the server addresses
        if server is None:
            self.serverAddr = self.cfg.get('def_srv_addr')
        else:
            self.serverAddr = server

        self.Socket  = None
        self.timeout = timeout

    def call(self, module, func, *args):
        '''Call the remote function'''
        self._open()
        ret = self.send((bert.Atom('call'), module, func, args))
        if len(ret) < 2 or ret[0] != 'reply':
            raise 1/0
        return ret[1]

    def cast(self, module, func, *args):
        '''Call the remote function'''
        self._open()
        ret = self.send((bert.Atom('cast'), module, func, args))
        if len(ret) != 1 or ret[0] != 'noreply':
            raise 1/0
        return ret[1]

    def _open(self):
        '''Open a connection to the server'''
        # If the connection is already open....
        if self.Socket != None:
            return self.Socket

        try:
            self.Socket = socket(AF_INET, SOCK_STREAM)
            self.Socket.setsockopt(SOL_SOCKET,SO_KEEPALIVE,1)
        except:
            raise

        try:
            self.Socket.connect(self.serverAddr)
        except:
            raise

        return self.Socket

    def send(self, msg):
        '''Send the BERP to the socket'''
        if msg is None:
            print("Error: Trying to send None message!")
            return None

        bmsg = bert.encode(msg)
        size = struct.pack("!L",len(bmsg))

        # Send the size header
        try:
            self.Socket.send(size)
        except:
            print("Exception: Socket send size failed (%s)." % (str(msg)))
            self._close()
            raise

        # Send the body
        try:
            while len(bmsg) > 0:
                cs = self.Socket.send(bmsg)
                bmsg = bmsg[cs:]
        except:
            print("Exception: Socket send data failed (%s)." % (bmsg))
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

        try:
            data = ''
            while len(data) < size:
                data = data + self.Socket.recv(size - len(data))
        except:
            self._close()
            raise InternalError, "Failed to receive reply"

        return bert.decode(data)

    def _close(self):
        if self.Socket:
            try:
                self.Socket.shutdown(2)
                self.Socket.close()
                print("Socket closed.")
            except:
                print("Exception: Socket close failed.")

        self.Socket = None


if __name__ == '__main__':
    brpc = BertRpcServer()

