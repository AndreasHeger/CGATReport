#!/bin/env python
import sys, os, imp, cStringIO, re, types, glob, optparse, shutil

USAGE = """python %s [OPTIONS] rst-document

clean all data associated with an rst document.

""" % sys.argv[0]

from SphinxReport.Tracker import Tracker
from SphinxReport.Renderer import *

if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-t", "--target", dest="target", type="choice",
                        choices = ("clean", "distclean" ),
                        help="cleaning target [default=%default]" )

    parser.set_defaults( target = "clean" )
        
    (options, args) = parser.parse_args()

    if len(args) == 1:
        options.target = args[0]
        
    dirs = []
    if options.target in ("clean", "distclean"):
        dirs.append( "_build" )
        
    if options.target in ("distclean",):
        dirs.append( "_cache" )
        dirs.append( "_static" )
                
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree( d )

                  
if __name__ == "__main__":
    sys.exit(main())
