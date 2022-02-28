# Copyright: see copyright.txt

import os
import sys
import pathlib
import logging
from optparse import OptionParser

import symbolic
import symbolic.loader
from symbolic.explore import ExplorationEngine

print("PyExZ3-Vu (Python Exploration with Z3)")

# sys.path = [os.path.abspath(os.path.join(os.path.dirname(__file__)))] + sys.path

usage = "usage: %prog [options] <path to a *.py file>"
parser = OptionParser(usage=usage)

parser.add_option("-l", "--log", dest="logfile", action="store", help="Save log output to a file", default="")
parser.add_option("-s", "--start", dest="entry", action="store", help="Specify entry point", default="")
parser.add_option("-g", "--graph", dest="dot_graph", action="store_true", help="Generate a DOT graph of execution tree")
parser.add_option("-m", "--max-iters", dest="max_iters", type="int", help="Run specified number of iterations", default=0)

(options, args) = parser.parse_args()

if options.logfile:
	logging.basicConfig(filename=options.logfile, level=logging.INFO)

filename = pathlib.Path(args[0])
if len(args) == 0 or not filename.is_file():
    parser.error("Missing app to execute")
    sys.exit(1)
filename = filename.resolve()
	
# Get the object describing the application
app = symbolic.loader.loaderFactory(filename, options.entry)
if app is None:
    sys.exit(1)

print(f"Exploring {app.filename}.{app.entry}")

result = None
try:
	engine = ExplorationEngine(app.createInvocation())
	generatedInputs, returnVals, path = engine.explore(options.max_iters)
	# check the result
	result = app.executionComplete(returnVals)

	# output DOT graph
	if (options.dot_graph):
		file = open(filename + ".dot", "w")
		file.write(path.toDot())	
		file.close()

except ImportError as e:
	# createInvocation can raise this
	logging.error(e)
	sys.exit(1)

if result is None or result == True:
	sys.exit(0);
else:
	sys.exit(1);	
