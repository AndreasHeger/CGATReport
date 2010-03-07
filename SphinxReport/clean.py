#!/bin/env python

"""
sphinxreport-clean
==================

:command:`sphinxreport-clean` removes all documents associated
with :class:`Tracker` thus allowing it to be re-built the next
time :command:`sphinx` is invoked as::

   sphinxreport-clean [clean|distclean|cache|Tracker1] [Tracker2] [...]

The full list of command line options is listed by suppling :option:`-h/--help`
on the command line.

If there is only one target and it is ``clean``, ``distclean``,
the full build we cleaned up. If it is ``cache``, only the cache
will be cleaned forcing newly built :class:`Tracker` objects to recompute
their data.

Alternatively, if one or more than one :class:`Tracker` is given, all 
documents referencing these will be removed to force a re-built next
time :command:`sphinx` is invoked. The names can contain shell-like
regular expression patterns (see glob in the python reference).
"""

import sys, os, imp, cStringIO, re, types, glob, optparse, shutil

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from SphinxReport.Tracker import Tracker
# from SphinxReport.Renderer import *

if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

SEPARATOR="@"

def deleteFiles( test_f, dirs_to_check = (".",), dry_run = False ):
    """remove all files that test_f returns True for.
    """
    removed = []
    for d in dirs_to_check:
        for root, dirs, files in os.walk(d):
            for f in files:
                if test_f( f ):
                    try:
                        ff = os.path.join( root, f) 
                        if not dry_run: os.remove( ff )
                        removed.append( ff )
                    except OSError, msg:
                        pass

    return removed

def removeTracker( tracker, dry_run = False ):
    """remove all files created by :class:Renderer objects
    that use tracker.
    """
    # get locations
    dirs_to_check = ("_static", "_cache", "_build" )

    # image and text files
    rx1 = re.compile("-%s%s" % (tracker,SEPARATOR) )
    # files in cache
    rx2 = re.compile("-%s$" % (tracker) )
    # .code files
    rx3 = re.compile("-%s%s" % (tracker,".code") )
    # .html files
    rx4 = re.compile("-%s%s" % (tracker,".html") )

    test_f = lambda x: rx1.search(x) or rx2.search(x) or rx3.search(x) or rx4.search(x)

    return deleteFiles( test_f, dirs_to_check, dry_run = dry_run )

def removeText( tracker, dry_run = False ):
    """remove all files that reference the ``tracker``."""
    
    # find all .rst files that reference tracker
    nremoved = 0
    rx_tracker = re.compile( tracker )
    files_to_check = []
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith( source_suffix ):
                fn = os.path.join( root, f )
                found = rx_tracker.search( "".join(open(fn,"r").readlines()) )
                if found:
                    files_to_check.append( f )

    suffixes = (".doctree", ".html" )
    patterns = []
    for f in files_to_check:
        p = f[:-len(source_suffix)]
        for s in suffixes:
            patterns.append( re.compile( "%s%s$" % (p, s ) ))

    def test_f(x):
        for p in patterns:
            if p.search(x): return True
        return False

    dirs_to_check = ("_build",)

    return deleteFiles( test_f, dirs_to_check, dry_run = dry_run )

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-v", "--verbose", dest="loglevel", type="int",
                       help="loglevel. The higher, the more output [default=%default]" )

    parser.add_option( "-s", "--section", dest="sections", type="choice", action="append",
                       choices=("tracker", "text"),
                       help="only clean from certain sections [default=%default]" )

    parser.add_option( "-n", "--dry-run", dest="dry_run", action="store_true",
                       help="only show what is about to be deleted, but do not delete [default=%default]" )

    parser.set_defaults( loglevel = 2,
                         dry_run = False,
                         sections = [] )

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

        if options.dry_run:
            print "the following directories will be deleted:"
            print "\n".join( dirs )
        else:
            for d in dirs:
                if os.path.exists(d):
                    shutil.rmtree( d )

    else:
        if options.dry_run:
            print "the following files will be deleted:"

        for tracker in args:
            print "cleaning up %s ..." % tracker,
            removed = []
            if not options.sections or "tracker" in options.sections:
                removed.extend( removeTracker( tracker, dry_run = options.dry_run ) )
            if not options.sections or "text" in options.sections:
                removed.extend( removeText( tracker, dry_run = options.dry_run ) )
            print "%i files (done)" % len(removed)
            if options.loglevel >= 3:
                print "\n".join( removed )
            if options.dry_run:
                print "\n".join( removed )
if __name__ == "__main__":
    sys.exit(main())
