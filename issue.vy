i: int128

@public
def __init__():
    self.i = 0

@public
@constant
def get_index() -> int128:
    return self.i

@public
def get_hash(n: string[20]) -> bytes32:
    return sha3(n)

@public
@payable
def get_hash2(n: string[20]) -> bytes32:
    return sha3(n)
