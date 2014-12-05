#!/bin/env python

"""
cgatreport-build
==================

:command:`cgatreport-build` is a pre-processor for restructured
texts. It implements parallel data gathering to speed up the
sphinx document creation process. It is invoked by simply prefixing
the:command:`sphinx` command line::

   cgatreport-build [OPTIONS] sphinx [SPHINX-OPTIONS]

The full list of command line options is listed by suppling:option:`-h/--help`
on the command line.

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
USAGE = """python %s [OPTIONS] args

build a sphinx report.

Building proceeds in three phases.

"""

from CGATReport import report_directive, gallery, clean, Utils

from CGATReport.Component import *

from CGATReport import Logger

try:
    from multiprocessing import Process
    from multiprocessing import Pool, Queue
except ImportError:
    from threading import Thread as Process

# import conf.py for source_suffix
if not os.path.exists("conf.py"):
    raise IOError("could not find conf.py")

exec(compile(open("conf.py").read(), "conf.py", 'exec'))

RST_TEMPLATE = """.. _%(label)s:

.. render:: %(tracker)s
:render: %(renderer)s
   %(options)s

   %(caption)s
"""

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s %(levelname)s %(message)s',
#     stream = open(Component.LOGFILE, "a") )


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

    try:
        for f, lineno, b, srcdir, builddir in work:
            ff = os.path.abspath(f)
            debug("build.run: profile: started: rst: %s:%i" % (ff, lineno))

            report_directive.run(b.mArguments,
                                 b.mOptions,
                                 lineno=lineno,
                                 content=b.mCaption,
                                 state_machine=None,
                                 document=ff,
                                 srcdir=srcdir,
                                 builddir=builddir)

            debug("build.run: profile: finished: rst: %s:%i" % (ff, lineno))

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
    try:
        infile = open(rst_file, "r")
    except IOError:
        print("could not open %s - skipped" % rst_file)
        return blocks

    for lineno, rst_block in rst_reader(infile):
        blocks.append((lineno, rst_block))
    infile.close()
    return blocks


class timeit:

    """simple timing+logging decorator"""

    def __init__(self, stage):
        self.mStage = stage

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            start = time.time()
            print("CGATReport: phase %s started" % (self.mStage))
            sys.stdout.flush()
            result = func(*args, **kwargs)
            print("CGATReport: phase %s finished in %i seconds" %
                  (self.mStage, time.time() - start))
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
    info("building plot elements started")

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
    for tracker, vals in work_per_tracker.items():
        work.append(vals)

    if len(work) == 0:
        return

    if options.num_jobs > 1:
        logQueue = Queue(100)
        handler = Logger.MultiProcessingLogHandler(
            logging.FileHandler(os.path.abspath(LOGFILE), "w"), logQueue)
    else:
        handler = logging.FileHandler(os.path.abspath(LOGFILE), "w")

    handler.setFormatter(
        logging.Formatter(LOGGING_FORMAT))

    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(options.loglevel)

    info('starting %i jobs on %i work items' % (options.num_jobs, len(work)))
    debug("build.py: profile: started: 0 seconds")

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
        print("CGATReport caught %i exceptions" % (len(errors)))
        print("## start of exceptions")
        for exception_name, exception_value, exception_stack in errors:
            print(exception_stack)
        print("## end of exceptions")
        sys.exit(1)

    if options.num_jobs > 1:
        counts = handler.getCounts()

        print(("CGATReport: messages: %i critical, %i errors, "
               "%i warnings, %i info, %i debug") %
              (counts["CRITICAL"],
               counts["ERROR"],
               counts["WARNING"],
               counts["INFO"],
               counts["DEBUG"]))

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
            code, tracker, tracker_path = report_directive.makeTracker(reference)
        except AttributeError:
            # ignore missing trackers
            nskipped += 1
            continue

        new_codehash = hashlib.md5("".join(code)).hexdigest()
        (basedir, fname, basename, ext,
         outdir, codename, notebookname) = report_directive.buildPaths(
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
            print("code has changed for %s: %i files removed" %
                  (reference, len(removed)))
            ncleaned += 1
    print("CGATReport: %i Trackers changed (%i tested, %i skipped)" %
          (ncleaned, ntested, nskipped))


def runCommand(command):
    try:
        retcode = subprocess.call(command, shell=True)
        if retcode < 0:
            warn("child was terminated by signal %i" % -retcode)
    except OSError(msg):
        fail("execution of %s failed: %s" % (cmd, msg))
        raise


@timeit("buildGallery")
def buildGallery(options, args):
    """construct the gallery page.
    """
    gallery.main()


@timeit("buildDocument")
def buildDocument(options, args):
    """construct the documents. This is simply done
    by calling sphinx-build.
    """
    runCommand("%s" % " ".join(args))


@timeit("buildLog")
def buildLog(options, args):
    """construct pages with the error log, stats
    and the build history.
    """
    runCommand("%s" % " ".join(args))


def main(argv=None):

    if argv is None:
        argv = sys.argv

    print("CGATReport: version %s started" % str("$Id$"))
    t = time.time()

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-a", "--num-jobs", dest="num_jobs", type="int",
                      help="number of parallel jobs to run [default=%default]")

    parser.add_option("-v", "--verbose", dest="loglevel", type="int",
                      help="loglevel. The higher, the more output "
                      "[default=%default]")

    parser.set_defaults(num_jobs=2,
                        loglevel=10,)

    parser.disable_interspersed_args()

    (options, args) = parser.parse_args()

    assert args[0].endswith(
        "sphinx-build"), "command line should contain sphinx-build"

    sphinx_parser = optparse.OptionParser(
        version="%prog version: $Id$", usage=USAGE)
    sphinx_parser.add_option("-b", type="string")
    sphinx_parser.add_option("-a")
    sphinx_parser.add_option("-E")
    sphinx_parser.add_option("-t", type="string")
    sphinx_parser.add_option("-d", type="string")
    sphinx_parser.add_option("-c", type="string")
    sphinx_parser.add_option("-C")
    sphinx_parser.add_option("-D", type="string")
    sphinx_parser.add_option("-A", type="string")
    sphinx_parser.add_option("-n")
    sphinx_parser.add_option("-Q")
    sphinx_parser.add_option("-q")
    sphinx_parser.add_option("-w", type="string")
    sphinx_parser.add_option("-W")
    sphinx_parser.add_option("-P")

    (sphinx_options, sphinx_args) = sphinx_parser.parse_args(args[1:])

    sourcedir = sphinx_args[0]

    rst_files = getDirectives(options, args, sourcedir)

    cleanTrackers(rst_files, options, args)

    buildPlots(rst_files, options, args, sourcedir)

    # buildGallery(options, args)

    # buildLog(options, args)

    buildDocument(options, args)

    print("CGATReport: finished in %i seconds" % (time.time() - t))

    debug("build.py: profile: finished: %i seconds" % (time.time() - t))

if __name__ == "__main__":
    sys.exit(main())
