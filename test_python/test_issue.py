import pytest
import sha3

@pytest.fixture
def privacy_contract(w3, get_contract):
    with open('issue.vy') as f:
        contract_code = f.read()
        contract = get_contract(contract_code)
    return contract

def k_hash(str, out='hex'):
    hh = sha3.keccak_256(str.encode('utf-8'))
    if out in ('hex','h','Hex','H'):
        return hh.hexdigest()
    else:
        return hh.digest()

def test_hash(privacy_contract):
    data = 'aaaa'
    hash = privacy_contract.get_hash(data).hex()
    s = k_hash(data)

    assert hash == s

def test_hash_2(privacy_contract,w3):
    def_account = w3.eth.accounts[0]
    value = int(.7 * 10**18)

    transaction = {
        'from': def_account,
        'gas': 20000000,
        'value': value
    }

    data = 'aaaa'
    hash = privacy_contract.get_hash2(data, transact=transaction).hex()
    s = k_hash(data)

    assert hash == s
