# Copyright: see copyright.txt
import settings
from collections import deque
import pdb

import helpers.vcommon as CM
from .z3_wrap import Z3Wrapper
from .symbolic_types import symbolic_type, SymbolicType
from .constraint import Constraint, PathToConstraint

mlog = CM.getLogger(__name__, settings.LOGGER_LEVEL)
DBG = pdb.set_trace

class FunctionInvocation:
    def __init__(self, function, reset):
        self.function = function
        self.reset = reset
        self.arg_constructor = {}
        self.initial_value = {}

    def callFunction(self, args):
        self.reset()
        return self.function(**args)

    def addArgumentConstructor(self, name, init, constructor):
        assert isinstance(init, int), init 

        self.initial_value[name] = init
        self.arg_constructor[name] = constructor

    @property
    def names(self):
        return self.arg_constructor.keys()

    def createArgumentValue(self, name, val=None):
        assert isinstance(name, str), name
        
        if val is None:
            val = self.initial_value[name]
        return self.arg_constructor[name](name, val)


class ExplorationEngine:
    def __init__(self, funcinv):
        self.invocation = funcinv
        # the input to the function

        # string -> SymbolicType
        self.symbolic_inputs = {n: funcinv.createArgumentValue(n) for n in funcinv.names}  
        self.constraints_to_solve = deque()
        self.num_processed_constraints = 0

        self.path = PathToConstraint(lambda c: self.addConstraint(c))
        # link up SymbolicObject to PathToConstraint in order to intercept control-flow
        symbolic_type.SymbolicObject.SI = self.path

        self.solver = Z3Wrapper()
        # outputs
        self.generated_inputs = []
        self.execution_return_values = []

    def addConstraint(self, constraint):
        assert isinstance(constraint, Constraint), constraint

        self.constraints_to_solve.append(constraint)
        # make sure to remember the input that led to this constraint
        constraint.inputs = self._getInputs()

    def explore(self, max_iterations=0):
        self._oneExecution()

        iterations = 1
        if max_iterations != 0 and iterations >= max_iterations:
            mlog.debug("Maximum number of iterations reached, terminating")
            return self.execution_return_values

        while not self._isExplorationComplete():
            selected = self.constraints_to_solve.popleft()
            if selected.processed:
                continue
            self._setInputs(selected.inputs)

            mlog.info(f"Selected constraint {selected}, {type(selected)}")
            asserts, query = selected.getAssertsAndQuery()
            print(asserts)
            print(query)
            model = self.solver.findCounterexample(asserts, query)

            if model is None:
                continue
            else:
                for name in model.keys():
                    self._updateSymbolicParameter(name, model[name])

            self._oneExecution(selected)

            iterations += 1
            self.num_processed_constraints += 1

            if max_iterations != 0 and iterations >= max_iterations:
                mlog.info("Maximum number of iterations reached, terminating")
                break

        return self.generated_inputs, self.execution_return_values, self.path

    # private

    def _updateSymbolicParameter(self, name, val):
        self.symbolic_inputs[name] = self.invocation.createArgumentValue(name, val)

    def _getInputs(self):
        return self.symbolic_inputs.copy()

    def _setInputs(self, d):
        self.symbolic_inputs = d

    def _isExplorationComplete(self):
        num_constr = len(self.constraints_to_solve)
        if num_constr == 0:
            mlog.info("Exploration complete")
            return True
        else:
            mlog.info("%d remaining constraints (total: %d, already solved: %d)" % (
                num_constr, self.num_processed_constraints + num_constr, self.num_processed_constraints))
            return False

    def _getConcrValue(self, v):
        assert isinstance(v, SymbolicType), v
        if isinstance(v, SymbolicType):
            return v.concrete_val
        else:
            return v

    def _recordInputs(self):
        args = self.symbolic_inputs
        inputs = [(k, self._getConcrValue(args[k])) for k in args]
        self.generated_inputs.append(inputs)
        print(inputs)
        DBG()

    def _oneExecution(self, expected_path=None):
        self._recordInputs()
        self.path.reset(expected_path)
        ret = self.invocation.callFunction(self.symbolic_inputs)
        print(ret)
        self.execution_return_values.append(ret)
