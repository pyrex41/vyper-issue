import sys
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from vyper import compiler
import sha3

def _w3():
    return Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

from web3.auto.gethdev import w3 as w

if len(sys.argv) > 1 :
    if sys.argv[1].lower() == 'geth':
        w3 = w
    else:
        w3 = _w3()
else:
    w3 = _w3()

with open('issue.vy') as f:
    source_code = f.read()


def deploy_contract(w3, source_code, *args, **kwargs):
    abi = compiler.mk_full_signature(source_code)
    bytecode = compiler.compile_code(source_code)['bytecode']
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    from_address = kwargs.pop('from',w3.eth.accounts[0])
    value = kwargs.pop('value',0)
    gasPrice = kwargs.pop('gasPrice', 0)

    transaction = {
        'from': from_address,
        'data': contract._encode_constructor_data(args, kwargs),
        'value': value,
        'gasPrice': gasPrice,
    }

    tx = w3.eth.sendTransaction(transaction)
    address = w3.eth.getTransactionReceipt(tx)['contractAddress']
    contract = w3.eth.contract(address, abi=abi, bytecode=bytecode)
    # Filter logs.
    contract._logfilter = w3.eth.filter({
        'fromBlock': w3.eth.blockNumber - 1,
        'address': contract.address
    })
    return contract

def k_hash(str, out='hex'):
    hh = sha3.keccak_256(str.encode('utf-8'))
    if out in ('hex','h','Hex','H'):
        return hh.hexdigest()
    else:
        return hh.digest()

def test_by_call(contract,func):
    print("--------------------------------------")
    print("Testing ", func.fn_name, " by calling: ")
    payload = 'aaaa'
    hash = func(payload).call().hex()
    python_hashed = k_hash(payload)

    if hash == python_hashed:
        print("Hashes match!")
        print(hash)
        return hash
    else:
        print("Hashes do not match:")
        print("Hash from contract: ", hash)
        print("Hash from python: ", python_hashed)
        return (hash, python_hashed)

def test_by_transact(contract,func,value=0):
    print("--------------------------------------")
    print("Testing ", func.fn_name, " by transacting: ")

    payload = 'aaaa'
    transaction = {
        'from': w3.eth.accounts[0],
        'gas': 200000,
        'value': value
    }

    hash = func(payload).transact(transaction).hex()
    python_hashed = k_hash(payload)

    if hash == python_hashed:
        print("Hashes match!")
        print(hash)
        return hash
    else:
        print("Hashes do not match:")
        print("Hash from contract: ", hash)
        print("Hash from python: ", python_hashed)
        return (hash, python_hashed)

def run_tests():
    args = ()
    kwargs = {}
    q = deploy_contract(w3, source_code, *args, **kwargs)
    get_hash = q.functions.get_hash
    get_hash2 = q.functions.get_hash2
    test_by_call(q,get_hash)
    test_by_call(q,get_hash2)
    test_by_transact(q,get_hash)
    test_by_transact(q,get_hash2,3*10**18)

run_tests()
