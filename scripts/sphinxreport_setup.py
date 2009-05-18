#!/bin/env python
import sys, re, os
import optparse

from pkg_resources import resource_string

import SphinxReport
import pkgutil

USAGE="""%s [OPTIONS]

set up an new pipebook.
""" % sys.argv[0]

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE)

    parser.add_option("-f", "--force", dest="force", action="store_true",
                      help="force overwrite of existing Makefile." )

    parser.add_option("-d", "--dest", dest="destination", type="string",
                      help="destination directory." )

    
    parser.set_defaults(
        destination = ".",
        force = False,
        )
    
    (options, args) = parser.parse_args()

    dest = options.destination

    # create directories
    for d in ("", "_templates", "labbook", "labbook/static", "analysis", "pipeline", "python" ):
        dd = os.path.join( dest, d )
        if not os.path.exists( dd ): os.makedirs( dd )

    # copy files
    def copy( src, dst ):
        fn = os.path.join( dest, dst, src)
        if os.path.exists( fn ):
            raise OSError( "file %s already exists - not overwriting." % fn )

        outfile = open( fn, "w" )
        outfile.write( pkgutil.get_data( "PipeBook", "templates/%s" % src) )
        outfile.close()

    for f in ("Makefile",
              "conf.py",
              "analysis.rst",
              "contents.rst",
              "pipeline.rst",
              "usage.rst"):
        copy( f, "" )

    for f in ("gallery.html",
              "index.html",
              "indexsidebar.html",
              "layout.html",
              "search.html" ):
        copy( f, "_templates")
        
    for f in ("Discussion.rst",
              "Introduction.rst",
              "Methods.rst",
              "Results.rst"):
        copy( f, "analysis")

    for f in ("PipelineTest.rst", ):
        copy( f, "pipeline")

    for f in ("theme.conf", ):
        copy( f, "labbook")

    for f in ("labbook.css", ):        
        copy( f, os.path.join("labbook", "static"))
        
    for f in ("Trackers.py", "Trackers.rst" ):
        copy( f, "python" )


    print """
Welcome to the PipeBook.

All files have been successfully copied to `%(dest)s`. In order to build the
pipebook, go to `%(dest)s`

cd %(dest)s

Optionally edit the configuration in *conf.py* as appropriate:

vi conf.py

As a first attempt, try to build the skeleton book:

make html gallery

If all works, you can start adding text to files in the
directories `analysis` and `pipeline` and pipeline.rst in the 
main directory. Add code to collect data to the module 'Trackers.py' 
in the  'python' directory. If you don't like the default file layout,
it can be easily changed.

""" % locals()

   

if __name__ == "__main__":
    sys.exit(main())
