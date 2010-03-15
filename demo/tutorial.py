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

ID = "$Id: tutorial.py 258 2010-03-14 08:44:17Z Roger $"
VER = "$Revision: 258 $"

import sys, time, socket
sys.path.append('..')
from bert_rpr import bert_rpr_finder, bert_rpc
from subprocess import Popen

# Tests ------------------------------------------------------------------------
print "\ntest 1: starting a BERT Remote Procedure Registry server on default port"
rpr = Popen(['python', '../bert_rpr/bert_rpr.py', '--verbose'])

time.sleep(3)   # Give the server time to start
# ------------------------------------------------------------------------------
print
print "test 2: Locate it using the finder, give it no clue to where the server is"
rprs = bert_rpr_finder.BertRprFinder(verbose=True).find()

# Check we found the correct one...
if len(rprs) > 0:
    if rprs[0][0] != socket.getfqdn() or rprs[0][1] != 48490:
        print "\tSome other RPR was found !!", rprs[0],(socket.getfqdn(),48490)
        sys.exit(20)
    print "\tThe RPR we started was found OK"
    registry = rprs[0]
else:
    print "\tError: No RPR found"
    sys.exit(21)

# ------------------------------------------------------------------------------
print
print "test 3: Ping the registry (Ping is supported as default by the registry)"
try:
    # reply = Registry.ping()
    reply = bert_rpc.BertRpcClient(registry).call('Registry', 'ping')
except socket.error, e:
    print "\tThe ping call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tPing replied with True as expected"
else:
    print "\tStrange! the ping call replied with %s" % (str(reply))
    sys.exit(30)

# ------------------------------------------------------------------------------
print
print "test 4: Tell the registry to terminate"
try:
    # reply = Registry.terminate()
    reply = bert_rpc.BertRpcClient(registry).call('Registry', 'terminate')
except socket.error, e:
    print "\tThe terminate call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tTerminate replied with True as expected"
else:
    print "\tStrange! the Terminate call replied with %s" % (reply)
    sys.exit(40)

time.sleep(5) # Give the server time to terminate

# ------------------------------------------------------------------------------
print
print "test 5: Ping the registry (Ping is supported as default by the registry)"
try:
    # reply = Registry.ping()
    reply = bert_rpc.BertRpcClient(registry).call('Registry', 'ping')
    print "\tError, could ping the RPR after shutdown"
except socket.error, e:
    print "\tThe ping call resulted in exception %s" % (str(e))
    print "\tAs expected"

# ------------------------------------------------------------------------------
print "\ntest 6: starting a BERT Remote Procedure Registry server on unexpected"
rpr = Popen(['python', '../bert_rpr/bert_rpr.py', '--verbose', '--port=49490'])

time.sleep(3)   # Give the server time to start
# ------------------------------------------------------------------------------
print
print "test 7: Locate it using the finder, give it no clue to where the server is"
rprs = bert_rpr_finder.BertRprFinder(verbose=True).find()

# Check we found the correct one...
if len(rprs) > 0:
    if rprs[0][0] != socket.getfqdn() or rprs[0][1] != 49490:
        print "\tSome other RPR was found !!", rprs[0],(socket.getfqdn(),49490)
        sys.exit(70)
    print "\tThe RPR we started was found OK"
    registry = rprs[0]
else:
    print "\tError: No RPR found"
    sys.exit(71)

# ------------------------------------------------------------------------------
print
print "test 8: Ping the registry (Ping is supported as default by the registry)"
try:
    # reply = Registry.ping()
    reply = bert_rpc.BertRpcClient(registry).call('Registry', 'ping')
except socket.error, e:
    print "\tThe ping call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tPing replied with True as expected"
else:
    print "\tStrange! the ping call replied with %s" % (str(reply))
    sys.exit(80)

# ------------------------------------------------------------------------------
print
print "test 9: Register a BERT_RPC function with the RPR"
try:
    # reply = Registry.ping()
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'register',

                    'module',
                    'function',
                    'this is metadata',
                    socket.getfqdn(),
                    98765

                )
except socket.error, e:
    print "\tThe register call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tregister replied with True as expected"
else:
    print "\tStrange! the register call replied with %s" % (str(reply))
    sys.exit(90)

# ------------------------------------------------------------------------------
print
print "test 10: Locate a registered function"
try:
    # (host, port) = resolve(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'resolve',
                'module',
                'function'
                )
except socket.error, e:
    print "\tThe register call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tregister replied with one entry as expected"
else:
    print "\tError! register replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(100)

# ------------------------------------------------------------------------------
print
print "test 11: Register the same BERT_RPC function again"
try:
    # reply = Registry.ping()
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'register',

                    'module',
                    'function',
                    'this is metadata',
                    socket.getfqdn(),
                    98765

                )
except socket.error, e:
    print "\tThe register call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tregister replied with True as expected"
else:
    print "\tStrange! the register call replied with %s" % (str(reply))
    sys.exit(11)

# ------------------------------------------------------------------------------
print
print "test 12: Locate a registered function (should not return a duplicate)"
try:
    # (host, port) = resolve(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'resolve',
                'module',
                'function'
                )
except socket.error, e:
    print "\tThe register call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tregister replied with one entry as expected"
else:
    print "\tError! register replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(12)
# ------------------------------------------------------------------------------
print
print "test 13: get a list of registered modules"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_modules'
                )
except socket.error, e:
    print "\tThe get_modules call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_modules replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_modules replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(13)
# ------------------------------------------------------------------------------
print
print "test 14: get a list of registered functions"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_functions',
                'module'
                )
except socket.error, e:
    print "\tThe get_modules call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_modules replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_modules replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(14)

# ------------------------------------------------------------------------------
print
print "test 15: get the complete metadata"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata'                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_metadata replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(15)
# ------------------------------------------------------------------------------
print
print "test 16: get the metadata for a module"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata',
                'module'
                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_metadata replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(16)
# ------------------------------------------------------------------------------
print
print "test 17: get the metadata for a single function"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata',
                'module',
                'function'
                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_metadata replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(17)
# ------------------------------------------------------------------------------
print
print "test 18: Register many functions and modules"
host = socket.getfqdn()
functions = [
                ('integer_math', 'add',      'integer add', host, 98765),
                ('integer_math', 'subtract', 'integer subtract', host, 98765),
                ('integer_math', 'divide',   'integer divide', host, 98765),
                ('integer_math', 'multiply', 'integer multiply', host, 98765),
                ('float_math',   'add',      'float add', host, 98765),
                ('float_math',   'subtract', 'float subtract', host, 98765),
                ('float_math',   'divide',   'float divide', host, 98765),
                ('float_math',   'multiply', 'float multiply', host, 98765),
        ]
try:
    # reply = Registry.register()
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'register_many',
                functions
                )
except socket.error, e:
    print "\tThe register_many call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tregister_many replied with True as expected"
else:
    print "\tStrange! the register_many call replied with %s" % (str(reply))
    sys.exit(18)

# ------------------------------------------------------------------------------
print
print "test 19: Locate a registered function (should not return a duplicate)"
try:
    # (host, port) = resolve(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'resolve',
                'float_math',
                'divide'
                )
except socket.error, e:
    print "\tThe resolve call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tresolve replied with one entry as expected"
else:
    print "\tError! resolve replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(19)
# ------------------------------------------------------------------------------
print
print "test 20: get a list of registered modules"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_modules'
                )
except socket.error, e:
    print "\tThe get_modules call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 3:
    print "\tget_modules replied with 3 entries as expected"
    for i in reply[1]:
        print "\t%s" % (str(i))
else:
    print "\tError! get_modules replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(20)
# ------------------------------------------------------------------------------
print
print "test 21: get a list of registered functions"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_functions',
                'integer_math'
                )
except socket.error, e:
    print "\tThe get_functions call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 4:
    print "\tget_functions replied with 4 entries as expected"
    for i in reply[1]:
        print "\t%s" % (str(i))
else:
    print "\tError! get_functions replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(21)

# ------------------------------------------------------------------------------
print
print "test 22: get the complete metadata"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata'                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 9:
    print "\tget_metadata replied with 9 entries as expected"
    for i in reply[1]:
        print "\t%s" % (str(i))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(22)
# ------------------------------------------------------------------------------
print
print "test 23: get the metadata for a module"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata',
                'integer_math'
                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 4:
    print "\tget_metadata replied with 4 entries as expected"
    for i in reply[1]:
        print "\t%s" % (str(i))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(23)
# ------------------------------------------------------------------------------
print
print "test 24: get the metadata for a single function"
try:
    # (host, port) = get_modules(module, function)
    reply = bert_rpc.BertRpcClient(registry).call(
                'Registry',
                'get_metadata',
                'integer_math',
                'add'
                )
except socket.error, e:
    print "\tThe get_metadata call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and len(reply[1]) == 1:
    print "\tget_metadata replied with one entry as expected: %s" % (str(reply[1]))
else:
    print "\tError! get_metadata replied with %s entries: %s" % (len(reply[1]), str(reply[1]))
    sys.exit(24)
# ------------------------------------------------------------------------------
print
print "End: Terminate the registry"
try:
    # reply = Registry.terminate()
    reply = bert_rpc.BertRpcClient(registry).call('Registry', 'terminate')
except socket.error, e:
    print "\tThe terminate call resulted in exception %s" % (str(e))
    raise

if len(reply) > 1 and reply[1] == True:
    print "\tTerminate replied with True as expected"
else:
    print "\tStrange! the Terminate call replied with %s" % (reply)
    sys.exit(40)

time.sleep(5) # Give the server time to terminate
sys.exit(0)

