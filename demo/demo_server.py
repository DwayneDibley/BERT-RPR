
from bert_rpc import BertRpcServer

def add(a, b):
    return a+b

modules = {
    'arithmetic': {
        'add': add
        }
    }

if __name__ == '__main__':
    ds = BertRpcServer(modules).serve()