#!/bin/env python
import sys, os, imp, cStringIO, re, types, glob, optparse, shutil

USAGE = """python %s [OPTIONS] target

clean all data according to target.

""" % sys.argv[0]

from SphinxReport.Tracker import Tracker
from SphinxReport.Renderer import *

if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

SEPARATOR="@"

def removeTracker( tracker ):
    
    # get locations
    dirs_to_check = ("_static", "_cache", "_build" )

    # image and text files
    rx1 = re.compile("-%s%s" % (tracker,SEPARATOR) )
    # files in cache
    rx2 = re.compile("^%s$" % (tracker) )
    # .code files
    rx3 = re.compile("-%s%s" % (tracker,".code") )

    isTracker = lambda x: rx1.search(x) or rx2.search(x) or rx3.search(x)

    nremoved = 0
    for d in dirs_to_check:
        for root, dirs, files in os.walk(d):
            for f in files:
                if isTracker( f ):
                    try:
                        os.remove( os.path.join( root, f) )
                        nremoved += 1
                    except OSError, msg:
                        pass

    return nremoved

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.set_defaults()
        
    (options, args) = parser.parse_args()

    if len(args) == 0: 
        print USAGE
        raise ValueError("please supply at least one target.""")

    if len(args) == 1 and args[0] in ("clean", "distclean", "cache"):
        dirs = []
        target = args[0]
        if target in ("clean", "distclean"):
            dirs.append( "_build" )
        
        if target in ("cache", "distclean"):
            dirs.append( "_cache" )

        if target in ("distclean",):
            dirs.append( "_static/report_directive" )

        for d in dirs:
            if os.path.exists(d):
                shutil.rmtree( d )

    else:
        for tracker in args:
            print "cleaning up %s ..." % tracker,
            nremoved = removeTracker( tracker )
            print "%i files (done)" % nremoved
                  
if __name__ == "__main__":
    sys.exit(main())
