# Copyright: see copyright.txt
import pdb
from .symbolic_types import SymbolicObject
import settings
import helpers.vcommon as CM

mlog = CM.getLogger(__name__, settings.LOGGER_LEVEL)
DBG = pdb.set_trace
class Predicate:
    """Predicate is one specific ``if'' encountered during the program execution.
       """
    def __init__(self, st, result):
        assert isinstance(st, SymbolicObject), st
        assert isinstance(result, bool), result

        self.symtype = st
        self.result = result

    @property
    def myvars(self):
        return self.symtype.myvars

    def __eq__(self, other):
        if isinstance(other, Predicate):
            return self.result == other.result and self.symtype.symbolicEq(other.symtype)
        else:
            return False

    def __hash__(self):
        return hash(self.symtype)

    def __str__(self):
        return self.symtype.toString() + " (%s)" % (self.result)

    def __repr__(self):
        return self.__str__()

    def negate(self):
        """Negates the current predicate"""
        assert(self.result is not None)
        self.result = not self.result

class PathToConstraint:
    def __init__(self, add):
        self.constraints = {}
        self.add = add
        self.root_constraint = Constraint(None, None)
        self.current_constraint = self.root_constraint
        self.expected_path = None

    def reset(self, expected):
        self.current_constraint = self.root_constraint
        if expected is None:
            self.expected_path = None
        else:
            self.expected_path = []
            tmp = expected
            while tmp.predicate is not None:
                self.expected_path.append(tmp.predicate)
                tmp = tmp.parent

    def whichBranch(self, branch, symbolic_type):
        """ This function acts as instrumentation.
        Branch can be either True or False."""

        # add both possible predicate outcomes to constraint (tree)
        p = Predicate(symbolic_type, branch)
        p.negate()
        cneg = self.current_constraint.findChild(p)
        p.negate()
        c = self.current_constraint.findChild(p)

        if c is None:
            c = self.current_constraint.addChild(p)

            # we add the new constraint to the queue of the engine for later processing
            mlog.debug("New constraint: %s" % c)
            self.add(c)

        # check for path mismatch
        # IMPORTANT: note that we don't actually check the predicate is the
        # same one, just that the direction taken is the same
        if self.expected_path != None and self.expected_path != []:
            expected = self.expected_path.pop()
            # while not at the end of the path, we expect the same predicate result
            # at the end of the path, we expect a different predicate result
            done = self.expected_path == []
            if (not done and expected.result != c.predicate.result or
                    done and expected.result == c.predicate.result):
                print("Replay mismatch (done=", done, ")")
                print(expected)
                print(c.predicate)

        if cneg is not None:
            # We've already processed both
            cneg.processed = True
            c.processed = True
            mlog.debug("Processed constraint: %s" % c)

        self.current_constraint = c

class Constraint:
    cnt = 0
    """A constraint is a list of predicates leading to some specific
	   position in the code."""

    def __init__(self, parent, last_predicate):
        self.inputs = None
        self.predicate = last_predicate
        self.processed = False
        self.parent = parent
        self.children = []
        self.id = self.__class__.cnt
        self.__class__.cnt += 1

    def __eq__(self, other):
        """Two Constraints are equal iff they have the same chain of predicates"""
        if isinstance(other, Constraint):
            if not self.predicate == other.predicate:
                return False
            return self.parent is other.parent
        else:
            return False

    def getAssertsAndQuery(self):
        self.processed = True

        # collect the assertions
        asserts = []
        tmp = self.parent
        while tmp.predicate is not None:
            asserts.append(tmp.predicate)
            tmp = tmp.parent

        return asserts, self.predicate

    def getLength(self):
        if self.parent is None:
            return 0
        return 1 + self.parent.getLength()

    def __str__(self):
        return str(self.predicate) + "  (processed: %s, path_len: %d)" % (self.processed, self.getLength())

    def __repr__(self):
        s = repr(self.predicate) + " (processed: %s)" % (self.processed)
        if self.parent is not None:
            s += "\n  path: %s" % repr(self.parent)
        return s

    def findChild(self, predicate):
        for c in self.children:
            if predicate == c.predicate:
                return c
        return None

    def addChild(self, predicate):
        assert(self.findChild(predicate) is None)
        c = Constraint(self, predicate)
        self.children.append(c)
        return c
