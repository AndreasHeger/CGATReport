#!/bin/env python

"""
sphinxreport-build
==================

:command:`sphinxreport-build` is a pre-processor for restructured
texts. It implements parallel data gathering to speed up the 
sphinx document creation process. It is invoked by simply prefixing
the :command:`sphinx` command line::

   sphinxreport-build [OPTIONS] sphinx [SPHINX-OPTIONS]

The full list of command line options is listed by suppling :option:`-h/--help`
on the command line.
"""

import sys, os, re, types, glob, optparse, traceback, hashlib
import subprocess, logging, time, collections
from logging import warn, log, debug, info

import Logger

USAGE = """python %s [OPTIONS] args

build a sphinx report.

Building proceeds in three phases. 

"""

import matplotlib
import matplotlib.pyplot as plt

from SphinxReport import report_directive, gallery, clean, Reporter

try:
    from multiprocessing import Process
    from multiprocessing import Pool, Queue
except ImportError:
    from threading import Thread as Process

if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

RST_TEMPLATE = """.. _%(label)s:

.. render:: %(tracker)s
   :render: %(renderer)s
   %(options)s

   %(caption)s
"""

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( Reporter.LOGFILE, "a" ) )

class ReportBlock:
    '''quick and dirty parsing of rst of a report block.'''
    def __init__(self): 
        self.mLines = []
        self.mOptions = {}
        self.mArguments = None
        self.mCaption = []

    def append(self,v):
        s = v.strip()
        if s.startswith( ".. report::" ):
            self.mArguments = re.match( ".. report::\s+(\S+)", s ).groups()
        else:
            s = re.match( ":(\S+):\s*(\S*)", v.strip())
            if s:
                key, value = s.groups()
                self.mOptions[key] = value
            else:
                self.mCaption.append( v )
        self.mLines.append( v )
        
def run( work ):
    """run a set of worker jobs.
    """

    try:
        for f, b in work:
            debug( "starting: %s, %s" % (str(b.mArguments), str(b.mOptions) ) )
            report_directive.run(  b.mArguments,
                                   b.mOptions,
                                   lineno = 0,
                                   content = b.mCaption,
                                   state_machine = None,
                                   document = os.path.abspath( f ) )
        return None
    except:
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        exception_stack  = traceback.format_exc(exceptionTraceback)
        exception_name   = exceptionType.__module__ + '.' + exceptionType.__name__
        exception_value  = str(exceptionValue)
        return (exception_name, exception_value, exception_stack)

def rst_reader(infile ):
    """parse infile and extract the :render: block."""
    
    result = None
    keep = 0
    for line in infile:
        if line.startswith( ".. report::" ):
            if result: yield result
            keep = True
            result = ReportBlock()
            result.append( line )
        else:
            if keep: 
                if re.match( "^\S", line ):
                    keep = False
                else:
                    result.append( line )

    if result: yield result
    
def getBlocksFromRstFile( rst_file ):

    blocks = []
    try:
        infile = open( rst_file, "r" )
    except IOError:
        print "could not open %s - skipped" % rst_file 
        return blocks

    for rst_block in rst_reader( infile ):
        blocks.append( rst_block )
    infile.close()
    return blocks

class timeit:
    """simple timing+logging decorator"""
    def __init__( self, stage):
        self.mStage = stage

    def __call__(self, func):
        def wrapped( *args, **kwargs ):
            start = time.time()
            print "SphinxReport: phase %s started" % (self.mStage) 
            result = func( *args, **kwargs)
            print "SphinxReport: phase %s finished in %i seconds" % (self.mStage, time.time() - start)
            return result
        return wrapped

@timeit( "getDirectives" )
def getDirectives( options, args ):
    ''' getting directives.
    '''
    rst_files = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith( source_suffix ):
                rst_files.append( os.path.join( root, f) )
    return rst_files

@timeit( "buildPlots" )
def buildPlots( rst_files, options, args ):
    '''build all plot elements and tables.

    This can be done in parallel to some extent.
    '''
    info( "building plot elements started" )

    # build work. Group trackers of the same name together as
    # the python shelve module does not allow concurrent write
    # access and the cache files will get mangled.
    work_per_tracker = collections.defaultdict( list )
    for f in rst_files:
        for b in getBlocksFromRstFile( f ):
            work_per_tracker[b.mArguments].append( (f,b) )

    work = []
    for tracker,vals in work_per_tracker.iteritems():
        work.append( vals )

    if len(work) == 0: return

    if options.num_jobs > 1:
        logQueue = Queue(100)
        handler= Logger.MultiProcessingLogHandler(logging.FileHandler( os.path.abspath( Reporter.LOGFILE ), "w"), logQueue)
    else:
        handler= logging.FileHandler( os.path.abspath( Reporter.LOGFILE ), "w")

    handler.setFormatter(  
        logging.Formatter( '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                           datefmt='%m-%d %H:%M' ) )

    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(options.loglevel)
    logging.info('starting %i jobs on %i work items' % (options.num_jobs, len(work)))

    if options.num_jobs > 1:
        pool = Pool( options.num_jobs )
        errors = pool.map( run, work )
        pool.close()
        pool.join()
    else:
        errors = []
        for w in work: errors.append( run( w ) )

    errors = [ e for e in errors if e ]
            
    if errors:
        print "SphinxReport caught %i exceptions" % (len(errors))
        print "## start of exceptions"
        for exception_name, exception_value, exception_stack in errors:
            print exception_stack,
        print "## end of exceptions"
        sys.exit(1)

    if options.num_jobs > 1:
        counts = handler.getCounts()

        print "SphinxReport: messages: %i critical, %i errors, %i warnings, %i info, %i debug" \
            % (counts["CRITICAL"],
               counts["ERROR"],
               counts["WARNING"],
               counts["INFO"],
               counts["DEBUG"] )
    
    logging.shutdown()

@timeit( "cleanTrackers" )
def cleanTrackers( rst_files, options, args ):
    '''instantiate trackers and get code.'''
    trackers = set()
    for f in rst_files:
        for b in getBlocksFromRstFile( f ):
            trackers.add(b.mArguments[0])
            
    ntested, ncleaned, nskipped = 0, 0, 0
    for reference in trackers:

        try:
            code, tracker = report_directive.getTracker( reference )
        except AttributeError:
            # ignore missing trackers
            nskipped += 1
            continue

        new_codehash = hashlib.md5("".join(code)).hexdigest()
        basedir, fname, basename, ext, outdir, codename = report_directive.buildPaths( reference )
        codefilename = os.path.join( outdir, codename )
        ntested += 1
        if not os.path.exists( codefilename ): 
            nskipped += 1
            continue
        old_codehash = hashlib.md5("".join(open(codefilename, "r").readlines())).hexdigest()
        if new_codehash != old_codehash:
            removed = clean.removeTracker( reference )
            removed.extend( clean.removeText( reference ))
            print "code has changed for %s: %i files removed" % (reference, len(removed))
            ncleaned += 1
    print "SphinxReport: %i Trackers changed (%i tested, %i skipped)" % (ncleaned, ntested, nskipped)
                                   
def runCommand( command ):
    try:
        retcode = subprocess.call( command, shell=True)
        if retcode < 0:
            warn( "child was terminated by signal %i" % -retcode )
    except OSError, e:
        fail( "execution of %s failed" % cmd)
        raise

@timeit( "buildGallery" )
def buildGallery( options, args ):
    """construct the gallery page.
    """
    gallery.main()

@timeit( "buildDocument" )
def buildDocument( options, args ):
    """construct the documents. This is simply done
    by calling sphinx-build.
    """
    runCommand( "%s" % " ".join(args) )

@timeit( "buildLog" )
def buildLog( options, args ):
    """construct pages with the error log, stats
    and the build history.
    """
    runCommand( "%s" % " ".join(args) )

def main():

    print "SphinxReport: version %s started" % str("$Id$")
    t = time.time()

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-a", "--num-jobs", dest="num_jobs", type="int",
                       help="number of parallel jobs to run [default=%default]" )
 
    parser.add_option( "-v", "--verbose", dest="loglevel", type="int",
                       help="loglevel. The higher, the more output [default=%default]" )
 
    parser.set_defaults( num_jobs = 2,
                         loglevel = 10, )

    parser.disable_interspersed_args()
    
    (options, args) = parser.parse_args()

    rst_files = getDirectives( options, args )

    cleanTrackers( rst_files, options, args )

    buildPlots( rst_files, options, args )

    buildGallery( options, args )

    buildLog( options, args )

    buildDocument( options, args )

    print "SphinxReport: finished in %i seconds" % (time.time() - t )

if __name__ == "__main__":
    sys.exit(main())
