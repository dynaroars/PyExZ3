# Copyright: copyright.txt

import inspect
from collections import Counter
import sys
from .explore import FunctionInvocation
from .symbolic_types import SymbolicInteger, getSymbolic
import pdb

import settings
import helpers.vcommon as CM
mlog = CM.getLogger(__name__, settings.LOGGER_LEVEL)


DBG = pdb.set_trace

# The built-in definition of len wraps the return value in an int() constructor, destroying any symbolic types.
# By redefining len here we can preserve symbolic integer types.
import builtins
builtins.len = (lambda x: x.__len__())

class Loader:
    def __init__(self, filename, entry):
        assert filename.is_file(), filename
        assert isinstance(entry, str), entry

        self._filename = filename.stem
        self._entrypoint = self._filename if entry == "" else entry
        self._resetCallback(True)

    @property
    def filename(self):
        return self._filename

    @property
    def entry(self):
        return self._entrypoint

    def createInvocation(self):
        func = self.app.__dict__[self._entrypoint]
        argspec = inspect.getargspec(func)

        inv = FunctionInvocation(self._execute, self._resetCallback)
        # check to see if user specified initial values of arguments
        if "concrete_args" in func.__dict__:
            print("concrete args")
            for (f, v) in func.concrete_args.items():
                if f not in argspec.args:
                    print(f"Error in @concrete: {self._entrypoint} has no argument {f}")
                    raise ImportError()
                else:
                    self._initArgConcrete(inv, f, v)

        if "symbolic_args" in func.__dict__:
            print("symbolic args")
            for (f, v) in func.symbolic_args.items():
                if f not in argspec.args:
                    print("Error (@symbolic): " + self._entrypoint +
                          " has no argument named " + f)
                    raise ImportError()
                elif f in inv.names:
                    print(f"Argument {f} defined in both @concrete and @symbolic")
                    raise ImportError()
                else:
                    s = getSymbolic(v)
                    if (s is None):
                        print("Error at argument " + f + " of entry point " + self._entrypoint +
                              " : no corresponding symbolic type found for type " + str(type(v)))
                        raise ImportError()
                    self._initArgSymbolic(inv, f, v, s)
        
        for a in argspec.args:
            if a not in inv.names:
                self._initArgSymbolic(inv, a, 0, SymbolicInteger)
        return inv

    # need these here (rather than inline above) to correctly capture values in lambda
    @classmethod
    def _initArgConcrete(cls, inv, f, val):
        inv.addArgumentConstructor(f, val, lambda n, v: val)

    @classmethod
    def _initArgSymbolic(cls, inv, f, val, st):
        isinstance(inv, FunctionInvocation), inv
        inv.addArgumentConstructor(f, val, lambda n, v: st(n, v))

    def executionComplete(self, return_vals):
        if "expected_result" in self.app.__dict__:
            return self._check(return_vals, self.app.__dict__["expected_result"]())
        if "expected_result_set" in self.app.__dict__:
            return self._check(return_vals, self.app.__dict__["expected_result_set"](), False)
        else:
            print(f"{self._filename}.py contains no expected_result function")
            return None

    # -- private
    def _resetCallback(self, firstpass=False):
        self.app = None
        if firstpass and self._filename in sys.modules:
            print(f"{self._filename} already loaded")
            raise ImportError()
        try:
            if (not firstpass and self._filename in sys.modules):
                del(sys.modules[self._filename])
            self.app = __import__(self._filename)
            if (not self._entrypoint in self.app.__dict__ or
                    not callable(self.app.__dict__[self._entrypoint])):
                print(
                    f"File {self._filename} does not contain a function named {self._entrypoint}")
                raise ImportError()
        except Exception as arg:
            print(f"Couldn't import {self._filename}")
            print(arg)
            raise ImportError()

    def _execute(self, **args):
        return self.app.__dict__[self._entrypoint](**args)

    def _check(self, computed, expected, as_bag=True):
        b_c = Counter(computed)
        b_e = Counter(expected)
        if ((as_bag and b_c != b_e) or
                (not as_bag and set(computed) != set(expected))):
            print(f"----> {self.filename} test failed <------")
            print(f"Expected: {b_e}, found: {b_c}")
            return False
        else:
            print(f"{self.filename} test passed <---")
            return True

    @classmethod
    def mk(cls, filename, entry):
        assert filename.is_file() and filename.suffix == '.py', filename
        assert isinstance(entry, str), entry
        try:
            sys.path.insert(0, str(filename.parent))
            ret = cls(filename, entry)
            return ret
        except ImportError:
            sys.path = sys.path[1:]
            return None
