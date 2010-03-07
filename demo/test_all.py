
import sys
sys.path.append('..')
from bert_rpr import bert_rpc
from subprocess import Popen

# Tests ------------------------------------------------------------------------
print "test 1: Call the add method of the basic server (server not running"
res = bert_rpc.BertRpcClient().call('arithmetic', 'add', 2, 3)
print res

# ------------------------------------------------------------------------------
print "\ntest 1: starting basic server on default port"
Popen(['python', './demo_server.py'])

# ------------------------------------------------------------------------------
print "test 2: Call the add method of the basic server"
res = bert_rpc.BertRpcClient().call('arithmetic', 'add', 2, 3)

if res != 5:
    print "test_all: Error, call of arithmetic.add(2, 3) returned %s" % (res)
else:
    print "test_all: result = %s, OK" % (res)

# ------------------------------------------------------------------------------
print "\ntest 2: Check that an incorrect module name created the correct exception"
try:
    res = bert_rpc.BertRpcClient().call('arithmeticx', 'add', 2, 3)
except bert_rpc.ServerError, e:
    print "Got %s, OK" % (str(e[:3]))
except Exception, e:
    print "Unexpected exception: %s" % (str(e))
    raise

# ------------------------------------------------------------------------------
print "\ntest 3: Check that an incorrect function name created the correct exception"
try:
    res = bert_rpc.BertRpcClient().call('arithmetic', 'addx', 2, 3)
except bert_rpc.ServerError, e:
    print "Got %s, OK" % (str(e[:3]))
except Exception, e:
    print "Unexpected exception: %s" % (str(e))
    raise

# ------------------------------------------------------------------------------
print "\ntest 4: Call the add method with one parameter generates an exception"
try:
    res = bert_rpc.BertRpcClient().call('arithmetic', 'add', 2)
except bert_rpc.ServerError, e:
    print "Got %s, OK" % (str(e[:3]))
except Exception, e:
    print "Unexpected exception: %s" % (str(e))
    raise

# ------------------------------------------------------------------------------
print "\ntest 5: Call the add method with one parameter generates an exception"
try:
    res = bert_rpc.BertRpcClient().call('arithmetic', 'add', 2)
except bert_rpc.ServerError, e:
    print "Got %s, OK" % (str(e[:3]))
except Exception, e:
    print "Unexpected exception: %s" % (str(e))
    raise
