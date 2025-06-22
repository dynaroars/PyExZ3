# Copyright: copyright.txt

from . symbolic_type import SymbolicObject

# we use multiple inheritance to achieve concrete execution for any
# operation for which we don't have a symbolic representation. As
# we can see a SymbolicInteger is both symbolic (SymbolicObject) and
# concrete (int)


class SymbolicInteger(SymbolicObject, int):
    # since we are inheriting from int, we need to use new
    # to perform construction correctly
    def __new__(cls, name, v, expr=None):
        return int.__new__(cls, v)

    def __init__(self, name, v, expr=None):
        assert isinstance(name, str), name
        assert isinstance(v, int), v

        SymbolicObject.__init__(self, name, expr)
        self.cval = v

    @property
    def concrete_val(self):
        return self.cval
        
    @classmethod
    def wrap(cls, conc, sym):
        return cls("se", conc, sym)

    def __hash__(self):
        return hash(self.cval)

    def _op_worker(self, args, fun, op):
        return self._do_sexpr(args, fun, op, SymbolicInteger.wrap)
    
    def __neg__(self):
        return self._op_worker([0, self], lambda x, y: x - y, "-")

# now update the SymbolicInteger class for operations we
# will build symbolic terms for


ops = [("add",    "+"),
       ("sub",    "-"),
       ("mul",    "*"),
       ("mod",    "%"),
       ("floordiv", "//"),
       ("and",    "&"),
       ("or",     "|"),
       ("xor",    "^"),
       ("lshift", "<<"),
       ("rshift", ">>")]


def make_method(method, op, a):
    code = "def %s(self,other):\n" % method
    code += "   return self._op_worker(%s,lambda x,y : x %s y, \"%s\")" % (
        a, op, op)
    locals_dict = {}
    exec(code, globals(), locals_dict)
    setattr(SymbolicInteger, method, locals_dict[method])


for (name, op) in ops:
    method = f"__{name}__"
    make_method(method, op, "[self,other]")
    rmethod = f"__r{name}__"
    make_method(rmethod, op, "[other,self]")
