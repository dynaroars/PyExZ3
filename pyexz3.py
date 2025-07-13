# Copyright: see copyright.txt

import sys
import pathlib
import logging
import argparse

import settings
import helpers.vcommon
import symbolic
import symbolic.loader
from symbolic.explore import ExplorationEngine

if __name__ == "__main__":
    aparser = argparse.ArgumentParser("DynaPSE")
    ag = aparser.add_argument

    ag("inp", help=("input file .py"))

    # 0 Error #1 Warn #2 Info #3 Debug
    ag("-l", "--log_level",
        type=int,
        choices=range(5),
        default=3,
        help="set logger info")

    ag("-s", "--start",
        dest="entry",
        default="",
        help="Specify entry point")
    
    ag("-m", "--max-iters",
        dest="max_iters",
        type=int,
        help="Run specified number of iterations",
        default=0)

    args = aparser.parse_args()
    filename = pathlib.Path(args.inp)

    settings.LOGGER_LEVEL = helpers.vcommon.getLogLevel(3)
    mlog = helpers.vcommon.getLogger(__name__, settings.LOGGER_LEVEL)

    if not filename.is_file():
        mlog.error("Missing app to execute")
        sys.exit(1)
    filename = filename.resolve()
    # Get the object describing the application
    app = symbolic.loader.Loader.mk(filename, args.entry)
    if app is None:
        sys.exit(1)

    mlog.info(f"Exploring {app.filename}.{app.entry}")

    result = None
    try:
        engine = ExplorationEngine(app.createInvocation())
        generatedInputs, returnVals, path = engine.explore(max_iterations=0)
        # check the result
        result = app.executionComplete(returnVals)

    except ImportError as e:
        # createInvocation can raise this
        logging.error(e)
        sys.exit(1)

    if result is None or result is True:
        sys.exit(0)
    else:
        sys.exit(1)


