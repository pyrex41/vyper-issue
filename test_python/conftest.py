import pytest
import logging
import web3

from web3 import Web3

from web3.contract import (
    ConciseContract,
    ConciseMethod
)

from vyper import compiler

class VyperMethod(ConciseMethod):
    ALLOWED_MODIFIERS = {'call', 'estimateGas', 'transact', 'buildTransaction'}

    def __call__(self, *args, **kwargs):
        return self.__prepared_function(*args, **kwargs)

    def __prepared_function(self, *args, **kwargs):
        if not kwargs:
            modifier, modifier_dict = 'call', {}
            fn_abi = [x for x in self._function.contract_abi if x['name'] == self._function.function_identifier].pop()
            modifier_dict.update({'gas': fn_abi['gas'] * 1000})  # To make tests faster just supply some high gas value.
        elif len(kwargs) == 1:
            modifier, modifier_dict = kwargs.popitem()
            if modifier not in self.ALLOWED_MODIFIERS:
                raise TypeError(
                    "The only allowed keyword arguments are: %s" % self.ALLOWED_MODIFIERS)
        else:
            raise TypeError("Use up to one keyword argument, one of: %s" % self.ALLOWED_MODIFIERS)

        return getattr(self._function(*args), modifier)(modifier_dict)


class VyperContract(ConciseContract):
    def __init__(self, classic_contract, method_class=VyperMethod):
        super().__init__(classic_contract, method_class)

def zero_gas_price_strategy(web3, transaction_params=None):
    return 0 # zero gas price makes testing simpler.

@pytest.fixture
def w3():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    return w3

def _get_contract(w3, source_code, *args, **kwargs):
    abi = compiler.mk_full_signature(source_code)
    bytecode = compiler.compile_code(source_code)['bytecode']
    print(bytecode  )
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    value = kwargs.pop('value', 0)
    value_in_eth = kwargs.pop('value_in_eth', 0)
    value = value_in_eth * 10**18 if value_in_eth else value  # Handle deploying with an eth value.
    gasPrice = kwargs.pop('gasPrice', 0)
    deploy_transaction = {
        'from': w3.eth.accounts[0],
        'data': contract._encode_constructor_data(args, kwargs),
        'value': value,
        'gasPrice': gasPrice,
    }
    tx = w3.eth.sendTransaction(deploy_transaction)
    address = w3.eth.getTransactionReceipt(tx)['contractAddress']
    contract = w3.eth.contract(address, abi=abi, bytecode=bytecode,ContractFactoryClass=VyperContract)
    # Filter logs.
    contract._logfilter = w3.eth.filter({
        'fromBlock': w3.eth.blockNumber - 1,
        'address': contract.address
    })
    return contract

@pytest.fixture
def get_contract(w3):
    def get_contract(source_code, *args, **kwargs):
        return _get_contract(w3, source_code, *args, **kwargs)
    return get_contract
