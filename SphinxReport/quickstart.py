#!/bin/env python
import sys, re, os
import optparse

from pkg_resources import resource_string
from pkgutil import get_loader

USAGE="""%s [OPTIONS]

set up an new pipebook.
""" % sys.argv[0]

def my_get_data(package, resource):
    """Get a resource from a package.

    This is a wrapper round the PEP 302 loader get_data API. The package
    argument should be the name of a package, in standard module format
    (foo.bar). The resource argument should be in the form of a relative
    filename, using '/' as the path separator. The parent directory name '..'
    is not allowed, and nor is a rooted name (starting with a '/').

    The function returns a binary string, which is the contents of the
    specified resource.

    For packages located in the filesystem, which have already been imported,
    this is the rough equivalent of

        d = os.path.dirname(sys.modules[package].__file__)
        data = open(os.path.join(d, resource), 'rb').read()

    If the package cannot be located or loaded, or it uses a PEP 302 loader
    which does not support get_data(), then None is returned.
    """

    loader = get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None
    
    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)    
    return loader.get_data(resource_name)

## get_data only available in python >2.6
try:
    from pkgutil import get_data
except ImportError: 
    get_data = my_get_data

def main( argv = sys.argv ):

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE)

    parser.add_option("-d", "--dest", dest="destination", type="string",
                      help="destination directory." )

    
    parser.set_defaults(
        destination = ".",
        )
    
    (options, args) = parser.parse_args()

    dest = options.destination

    # create directories
    for d in ("", "_templates", "labbook", "labbook/static", "analysis", "pipeline", "trackers", "templates" ):
        dd = os.path.join( dest, d )
        if not os.path.exists( dd ): os.makedirs( dd )

    # copy files
    def copy( src, dst ):
        fn = os.path.join( dest, dst, src)
        if os.path.exists( fn ):
            raise OSError( "file %s already exists - not overwriting." % fn )

        outfile = open( fn, "w" )
        x = get_data( "SphinxReport", "templates/%s" % src)
        outfile.write( x )
        outfile.close()

    for f in ("Makefile",
              "server.py",
              "sphinxreport.ini",
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
        
    for f in ("data_table.html",):
        copy( f, "templates")

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
        copy( f, "trackers" )


    print """
Welcome to the PipeBook.

All files have been successfully copied to `%(dest)s`. In order to build the
pipebook, go to `%(dest)s`

cd %(dest)s

Optionally edit the configuration in *conf.py* as appropriate:

vi conf.py

As a first attempt, try to build the skeleton book:

make html

If all works, you can start adding text to files in the
directories `analysis` and `pipeline` and pipeline.rst in the 
main directory. Add code to collect data to the module 'Trackers.py' 
in the  'trackers' directory. If you don't like the default file layout,
it can be easily changed.

""" % locals()

   
if __name__ == "__main__":
    sys.exit(main())
