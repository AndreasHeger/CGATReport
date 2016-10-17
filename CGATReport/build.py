#!/bin/env python

"""cgatreport-build
==================

:command:`cgatreport-build` is a pre-processor for restructured
texts. It implements parallel data gathering to speed up the sphinx
document creation process. It is invoked by simply prefixing
the:command:`sphinx` command line::

   cgatreport-build [OPTIONS] sphinx [SPHINX-OPTIONS]

The full list of command line options is listed by
suppling:option:`-h/--help` on the command line.

**-a/--num-jobs** number of jobs
    Number of jobs to start for parallel pre-processing.

**-v/--verbose** verbosity level
    Increase the number of status messages displayed.

"""

import sys
import os
import re
import optparse
import traceback
import hashlib
import subprocess
import logging
import time
import collections
from multiprocessing import Pool, Queue
from CGATReport import Component

from sphinx.util.osutil import cd

from CGATReport import report_directive, clean, Utils
from CGATReport import Logger

source_suffix = ".rst"


class ReportBlock:

    '''quick and dirty parsing of rst of a report block.'''

    def __init__(self):
        self.mLines = []
        self.mOptions = {}
        self.mArguments = None
        self.mCaption = []

    def append(self, v):
        s = v.strip()
        if s.startswith(".. report::"):
            self.mArguments = re.match(".. report::\s+(\S+)", s).groups()
        else:
            s = re.match(":(\S+):\s*(\S*)", v.strip())
            if s:
                key, value = s.groups()
                self.mOptions[key] = value
            else:
                self.mCaption.append(v)
        self.mLines.append(v)


def run(work):
    """run a set of worker jobs.
    """
    logger = Component.get_logger()
    try:
        for f, lineno, b, srcdir, builddir in work:
            ff = os.path.abspath(f)
            logger.debug("build.run: profile: started: rst: %s:%i" % (ff, lineno))

            report_directive.run(b.mArguments,
                                 b.mOptions,
                                 lineno=lineno,
                                 content=b.mCaption,
                                 state_machine=None,
                                 document=ff,
                                 srcdir=srcdir,
                                 builddir=builddir)

            logger.debug("build.run: profile: finished: rst: %s:%i" % (ff, lineno))

        return None
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        exception_stack = traceback.format_exc(exceptionTraceback)
        exception_name = exceptionType.__module__ + \
            '.' + exceptionType.__name__
        exception_value = str(exceptionValue)
        return (exception_name, exception_value, exception_stack)


def rst_reader(infile):
    """parse infile and extract the:render: block."""

    result = None
    keep = 0
    lineno = 0
    for line in infile:
        lineno += 1
        if line.startswith(".. report::"):
            if result:
                yield lineno, result
            keep = True
            result = ReportBlock()
            result.append(line)
        else:
            if keep:
                if re.match("^\S", line):
                    keep = False
                else:
                    result.append(line)

    if result:
        yield lineno, result


def getBlocksFromRstFile(rst_file):

    blocks = []

    logger = Component.get_logger()
    logger.debug("reading {}".format(rst_file))

    try:
        with open(rst_file, "r") as infile:
            for lineno, rst_block in rst_reader(infile):
                blocks.append((lineno, rst_block))
    except IOError:
        print(("could not open %s - skipped" % rst_file))
        return blocks

    return blocks


class timeit:

    """simple timing+logging decorator"""

    def __init__(self, stage):
        self.mStage = stage

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            start = time.time()
            print(("CGATReport: phase %s started" % (self.mStage)))
            sys.stdout.flush()
            result = func(*args, **kwargs)
            print(("CGATReport: phase %s finished in %i seconds" %
                  (self.mStage, time.time() - start)))
            sys.stdout.flush()
            return result
        return wrapped


@timeit("getDirectives")
def getDirectives(options, args, sourcedir):
    ''' getting directives.
    '''
    rst_files = []
    for root, dirs, files in os.walk(sourcedir):
        for f in files:
            if f.endswith(source_suffix):
                rst_files.append(os.path.join(root, f))
    return rst_files


@timeit("buildPlots")
def buildPlots(rst_files, options, args, sourcedir):
    '''build all plot elements and tables.

    This can be done in parallel to some extent.
    '''
    logger = Component.get_logger()
    logger.info("building plot elements started")

    # build work. Group trackers of the same name together as
    # the python shelve module does not allow concurrent write
    # access and the cache files will get mangled.
    work_per_tracker = collections.defaultdict(list)
    for f in rst_files:
        for lineno, b in getBlocksFromRstFile(f):
            work_per_tracker[b.mArguments].append((f,
                                                   lineno,
                                                   b,
                                                   sourcedir,
                                                   "."))

    work = []
    for tracker, vals in list(work_per_tracker.items()):
        work.append(vals)

    if len(work) == 0:
        return

    logger = Component.get_logger()
    logger.setLevel(options.loglevel)

    if options.num_jobs > 1:
        logQueue = Queue(100)
        handler = Logger.MultiProcessingLogHandler(
            logging.FileHandler(
                os.path.abspath(Component.LOGFILE), "a"), logQueue)
        handler.setFormatter(
            logging.Formatter(Component.LOGGING_FORMAT))
        logger.addHandler(handler)

    logger.info(
        "starting %i jobs on %i work items" % (options.num_jobs, len(work)))
    logger.debug(
        "build.py: profile: started: 0 seconds")

    if options.num_jobs > 1:
        pool = Pool(options.num_jobs)
        # todo: async execution with timeouts
        # res = pool.map_async(run, work)
        errors = pool.map(run, work)
        pool.close()
        pool.join()
    else:
        errors = []
        for w in work:
            errors.append(run(w))

    errors = [e for e in errors if e]

    if errors:
        print(("CGATReport caught %i exceptions" % (len(errors))))
        print("## start of exceptions")
        for exception_name, exception_value, exception_stack in errors:
            print(exception_stack)
        print("## end of exceptions")
        sys.exit(1)

    if options.num_jobs > 1:
        counts = handler.getCounts()

        print((("CGATReport: messages: %i critical, %i errors, "
               "%i warnings, %i info, %i debug") %
              (counts["CRITICAL"],
               counts["ERROR"],
               counts["WARNING"],
               counts["INFO"],
               counts["DEBUG"])))

    logging.shutdown()


@timeit("cleanTrackers")
def cleanTrackers(rst_files, options, args):
    '''instantiate trackers and get code.'''
    trackers = set()
    for f in rst_files:
        for lineno, b in getBlocksFromRstFile(f):
            trackers.add(b.mArguments[0])

    ntested, ncleaned, nskipped = 0, 0, 0
    for reference in trackers:

        try:
            code, tracker, tracker_path = report_directive.makeTracker(
                reference)
        except AttributeError:
            # ignore missing trackers
            nskipped += 1
            continue

        new_codehash = hashlib.md5("".join(code)).hexdigest()
        (basedir, fname, basename, ext,
         outdir, codename, notebookname) = Utils.build_paths(
             reference)
        codefilename = os.path.join(outdir, codename)
        ntested += 1
        if not os.path.exists(codefilename):
            nskipped += 1
            continue
        old_codehash = hashlib.md5(
            "".join(open(codefilename, "r").readlines())).hexdigest()
        if new_codehash != old_codehash:
            removed = clean.removeTracker(reference)
            removed.extend(clean.removeText(reference))
            print(("code has changed for %s: %i files removed" %
                  (reference, len(removed))))
            ncleaned += 1
    print(("CGATReport: %i Trackers changed (%i tested, %i skipped)" %
          (ncleaned, ntested, nskipped)))


def runCommand(command):
    try:
        retcode = subprocess.call(command, shell=True)
        if retcode < 0:
            warn("child was terminated by signal %i" % -retcode)
    except OSError as msg:
        Component.get_logger().error(
            "execution of %s failed: %s" % (command, msg))
        raise


@timeit("buildDocument")
def buildDocument(options, args):
    """construct the documents. This is simply done
    by calling sphinx-build.
    """
    runCommand("%s" % " ".join(args))


def main(argv=None):


    logger = Component.get_logger()
    if argv is None:
        argv = sys.argv

    print(("CGATReport: version %s started" % str("$Id$")))
    t = time.time()

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

    sphinx_parser = optparse.OptionParser(
        version="%prog version: $Id$",
        usage=globals()["__doc__"])

    sphinx_parser.add_option("-b", type="string")
    sphinx_parser.add_option("-a")
    sphinx_parser.add_option("-E")
    sphinx_parser.add_option("-t", type="string")
    sphinx_parser.add_option("-d", type="string")
    sphinx_parser.add_option("-c", dest="confdir", type="string")
    sphinx_parser.add_option("-C")
    sphinx_parser.add_option("-D", type="string")
    sphinx_parser.add_option("-A", type="string")
    sphinx_parser.add_option("-n")
    sphinx_parser.add_option("-Q")
    sphinx_parser.add_option("-q")
    sphinx_parser.add_option("-w", type="string")
    sphinx_parser.add_option("-W")
    sphinx_parser.add_option("-P")
    sphinx_parser.add_option("-j", dest="num_jobs", type="int")

    sphinx_parser.set_defaults(
        confdir=None)

    (sphinx_options, sphinx_args) = sphinx_parser.parse_args(args[1:])

    sourcedir = sphinx_args[0]
    # local conf.py overrides anything
    if os.path.exists("conf.py"):
        sphinx_options.confdir = "."
    elif sphinx_options.confdir is None:
        sphinx_options.confdir = sourcedir

    # import conf.py for source_suffix
    config_file = os.path.join(sphinx_options.confdir, "conf.py")
    if not os.path.exists(config_file):
        raise IOError("could not find {}".format(config_file))

    config = {"__file__": config_file}
    with cd(sphinx_options.confdir):
        exec(compile(open(os.path.join(config_file)).read(),
                     "conf.py", 'exec'), config)

    rst_files = getDirectives(options, args, sourcedir)

    Utils.get_parameters()

    cleanTrackers(rst_files, options, args)

    buildPlots(rst_files, options, args, sourcedir)

    buildDocument(options, args)

    print(("CGATReport: finished in %i seconds" % (time.time() - t)))

    logger.debug(
        "build.py: profile: finished: %i seconds" % (time.time() - t))

if __name__ == "__main__":
    sys.exit(main())
