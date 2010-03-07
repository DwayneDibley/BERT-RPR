
import bert_rpc

if __name__ == '__main__':
    res = bert_rpc.BertRpcClient().call('arithmetic', 'add', 2, 3)
    print "result =", res