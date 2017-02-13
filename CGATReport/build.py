#!/bin/env python

"""cgatreport-build
==================

:command:`cgatreport-build` used to be a pre-processor for restructured
texts. It has now been deprecated. The current implementation simply
calls sphinx.

"""

import sys
import optparse
import subprocess
from logging import warn
from CGATReport import Component


def main(argv=None):

    if argv is None:
        argv = sys.argv

    parser = optparse.OptionParser(version="%prog version: $Id$",
                                   usage=globals()["__doc__"])

    parser.add_option("-j", "-a", "--num-jobs", dest="num_jobs", type="int",
                      help="number of parallel jobs to run [default=%default]")

    parser.add_option("-v", "--verbose", dest="loglevel", type="int",
                      help="loglevel. The higher, the more output "
                      "[default=%default]")

    parser.set_defaults(num_jobs=2,
                        loglevel=10,)

    parser.disable_interspersed_args()

    (options, args) = parser.parse_args(argv[1:])

    assert args[0].endswith(
        "sphinx-build"), "command line should contain sphinx-build"

    command = " ".join(args)

    try:
        retcode = subprocess.call(command, shell=True)
        if retcode < 0:
            warn("child was terminated by signal %i" % -retcode)
    except OSError as msg:
        Component.get_logger().error(
            "execution of %s failed: %s" % (command, msg))
        raise


if __name__ == "__main__":
    sys.exit(main())
