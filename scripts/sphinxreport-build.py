#!/bin/env python
import sys, os, imp, cStringIO, re, types, glob, optparse
import subprocess, logging, time
from logging import warn, log, debug, info

USAGE = """python %s [OPTIONS] args

build a sphinx report.

Building proceeds in three phases. 

"""

import matplotlib
import matplotlib.pyplot as plt



from SphinxReport import report_directive

try:
    from multiprocessing import Process
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
    stream = open( "sphinxreport.log", "a" ) )

class ReportBlock:
    """quick and dirty parsing of rst of a report block."""
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
    """run a set of worker jobs."""

    for f, b in work:
        report_directive.run(  b.mArguments,
                               b.mOptions,
                               lineno = 0,
                               content = b.mCaption,
                               state_machine = None,
                               document = os.path.abspath( f ) )
    

def rst_reader(infile ):
    """parse infile and extract the :render: block."""
    
    result = ReportBlock()
    keep = 0
    for line in infile:
        if line.startswith( ".. report::" ):
            keep = True
            result.append( line )
            continue

        if keep: 
            if re.match( "^\S", line ):
                keep = False
                result.append( line ) 
                yield result
                result = ReportBlock()
            else:
                result.append( line )

    if keep: yield result

def getBlocksFromRstFile( rst_file ):

    blocks = []
    infile = open( rst_file, "r" )
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

@timeit( "buildPlots" )
def buildPlots( options, args ):
    """build all plot elements and tables.

    This can be done in parallel.
    """
    info( "building plot elements started" )

    rst_files = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith( source_suffix ):
                rst_files.append( os.path.join( root, f) )
    
    work = []
    for f in rst_files:
        blocks = getBlocksFromRstFile( f )
        for b in blocks:
            work.append( (f, b) )

    if len(work) == 0: return

    cs = len(work) // options.num_jobs
    processes = []
    for x in range( 0, len(work), cs ):

        p = Process( target = run, args = ( work[x:x+cs], ) )
        processes.append( p )
        p.start()

    for p in processes: p.join()


def runCommand( command ):
    try:
        retcode = subprocess.call( command, shell=True)
        if retcode < 0:
            warn( "Child was terminated by signal %i" % -retcode )
    except OSError, e:
        fail( "Execution of %s failed" % cmd)
        raise

@timeit( "buildGallery" )
def buildGallery( options, args ):
    """construct the gallery page.
    """
    runCommand( "sphinxreport-gallery.py" )

@timeit( "buildDocument" )
def buildDocument( options, args ):
    """construct the documents. This is simply done
    by calling sphinx-build.
    """
    runCommand( "%s" % " ".join(args) )

def main():

    print "SphinxReport: version %s started" % str("$Id$")
    t = time.time()

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-a", "--num-jobs", dest="num_jobs", type="int",
                       help="number of parallel jobs to run [default=%default]" )

    parser.set_defaults( num_jobs = 2 )

    parser.disable_interspersed_args()
    
    (options, args) = parser.parse_args()

    buildPlots( options, args )

    buildGallery( options, args )

    buildDocument( options, args )

    print "SphinxReport: finished in %i seconds" % (time.time() - t )

if __name__ == "__main__":
    sys.exit(main())
