# Copyright: see copyright.txt

from .symbolic_int import SymbolicInteger
from .symbolic_int import SymbolicObject
from .symbolic_dict import SymbolicDict
from .symbolic_str import SymbolicStr
from .symbolic_type import SymbolicType

SymbolicObject.wrap = lambda conc, sym: SymbolicInteger("se", conc, sym)

def getSymbolic(v):
    exported = [(int, SymbolicInteger),
                (dict, SymbolicDict), 
                (str, SymbolicStr)]
    for (t, s) in exported:
        if isinstance(v, t):
            return s
    return None
