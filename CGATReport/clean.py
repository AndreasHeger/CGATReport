#!/bin/env python

"""
cgatreport-clean
==================

:command:`cgatreport-clean` removes all documents associated
with:class:`Tracker` thus allowing it to be re-built the next
time:command:`sphinx` is invoked as::

   cgatreport-clean [clean|distclean|cache|Tracker1] [Tracker2] [...]

The full list of command line options is listed by suppling:option:`-h/--help`
on the command line.

The options are:

**-v/--verbose** verbosity level
   Increase the number of status messages displayed.

**-n/--dry-run**
   Show all files that will be removed but do not remove them.

**-s/--section** choice
   Only clean within certain types of documents. The default is all. Possible choices are
   ``tracker`` and ``text``.

**-b/--build** path
   Path to build directory. By default, documents are examined in the current directory.


**-w/--path** path
   Path with restructured document. By default, the ``.rst`` files are assumed to reside
   in the current directory. Without the documents, the clean command will not be able
   to remove all documents that refer to a:term:`tracker`.

If there is only one target and it is ``clean``, ``distclean``,
the full build we cleaned up. If it is ``cache``, only the cache
will be cleaned forcing newly built:class:`Tracker` objects to recompute
their data.

Alternatively, if one or more than one:class:`Tracker` is given, all
documents referencing these will be removed to force a re-built next
time:command:`sphinx` is invoked.

Trackers are interpreted as patterns. For example,
the following will remove all data from the cache and all previously build
documents containing trackers matching the word ``OldData``::

   cgatreport-clean OldData

"""

import sys
import os
import imp
import io
import re
import types
import glob
import optparse
import shutil

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from CGATReport.Tracker import Tracker

SEPARATOR = "@"

# import conf.py for source_suffix
source_suffix = ".rst"
if os.path.exists("conf.py"):
    try:
        exec(compile(open("conf.py").read(), "conf.py", 'exec'))
    except ValueError:
        pass

RSTDIR = "."
if "docsdir" in locals():
    RSTDIR = docsdir


def deleteFiles(test_f, dirs_to_check=(".",), dry_run = False):
    """remove all files that test_f returns True for.
    """
    removed = []
    for d in dirs_to_check:
        for root, dirs, files in os.walk(d):
            for f in files:
                if test_f(f):
                    try:
                        ff = os.path.join(root, f)
                        if not dry_run:
                            os.remove(ff)
                        removed.append(ff)
                    except OSError as msg:
                        pass

    return removed


def removeTracker(tracker,
                  dry_run=False,
                  builddir="report"):
    """remove all files created by:class:Renderer objects
    that use tracker.
    """
    # get locations
    # this is a patch - add configuration options from conf.py
    dirs_to_check = ("_static", "_cache", "_build", builddir)

    pattern = ".*%s.*" % tracker
    # image and text files
    rx1 = re.compile("_%s%s" % (pattern, SEPARATOR))
    # files in cache
    rx2 = re.compile("_%s$" % (pattern))
    # .code files
    rx3 = re.compile("_%s%s" % (pattern, ".code"))
    # .html files
    rx4 = re.compile("_%s%s" % (pattern, ".html"))
    test_f = lambda x: rx1.search(x) or rx2.search(
        x) or rx3.search(x) or rx4.search(x)

    return deleteFiles(test_f, dirs_to_check, dry_run=dry_run)


def removeText(pattern,
               dry_run=False,
               sourcedir=".",
               builddir="report",
               suffix=".rst"):
    """remove all files that contain the ``pattern``."""

    # find all .rst files that reference tracker
    nremoved = 0
    rx_tracker = re.compile(pattern)
    files_to_check = []
    for root, dirs, files in os.walk(sourcedir):
        for f in files:
            if f.endswith(suffix):
                fn = os.path.join(root, f)
                try:
                    data = "".join(open(fn, "r").readlines())
                except IOError:
                    continue

                found = rx_tracker.search(data)

                if found:
                    files_to_check.append(f)

    suffixes = (".doctree", ".html")
    patterns = []
    for f in files_to_check:
        p = f[:-len(suffix)]
        for s in suffixes:
            patterns.append(re.compile("%s%s$" % (p, s)))

    def test_f(x):
        for p in patterns:
            if p.search(x):
                return True
        return False

    dirs_to_check = (builddir,)

    return deleteFiles(test_f, dirs_to_check, dry_run=dry_run)


def main():

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-v", "--verbose", dest="loglevel", type="int",
                      help="loglevel. The higher, the more output [default=%default]")

    parser.add_option("-s", "--section", dest="sections", type="choice", action="append",
                      choices=("tracker", "text", "doctree"),
                      help="only clean from certain sections [default=%default]")

    parser.add_option("-p", "--path", dest="path", type="string",
                      help="path to rst source [default=%default]")

    parser.add_option("-b", "--build", dest="builddir", type="string",
                      help="path to build dir [default=%default]")

    parser.add_option("-n", "--dry-run", dest="dry_run", action="store_true",
                      help="only show what is about to be deleted, but do not delete [default=%default]")

    parser.set_defaults(loglevel=2,
                        dry_run=False,
                        path=RSTDIR,
                        builddir=".",
                        sections=[])

    (options, args) = parser.parse_args()

    if len(args) == 0:
        print(USAGE)
        raise ValueError("please supply at least one target.""")

    if len(args) == 1 and args[0] in ("clean", "distclean", "cache"):
        dirs = []
        target = args[0]
        if target in ("clean", "distclean"):
            dirs.append("_build")

        if target in ("cache", "distclean"):
            dirs.append("_cache")

        if target in ("distclean",):
            dirs.append("_static/report_directive")

        if options.dry_run:
            print("the following directories will be deleted:")
            print(("\n".join(dirs)))
        else:
            for d in dirs:
                if os.path.exists(d):
                    shutil.rmtree(d)

    else:
        if options.dry_run:
            print("the following files will be deleted:")

        for tracker in args:
            print(("cleaning up %s ..." % tracker))
            removed = []
            if not options.sections or "tracker" in options.sections:
                if options.loglevel >= 2:
                    print("removing trackers")
                removed.extend(removeTracker(tracker, dry_run=options.dry_run))
            if not options.sections or "doctree" in options.sections:
                if options.loglevel >= 2:
                    print("removing doctrees")
                removed.extend(removeText(tracker,
                                          dry_run=options.dry_run,
                                          sourcedir=options.builddir,
                                          builddir=options.builddir,
                                          suffix=".doctree"))
            if not options.sections or "text" in options.sections:
                if options.loglevel >= 2:
                    print("removing rst")
                if options.loglevel >= 2:
                    print(("sourcedir=%s" % options.path))
                removed.extend(removeText(tracker,
                                          dry_run=options.dry_run,
                                          sourcedir=options.path,
                                          builddir=options.builddir,
                                          suffix=source_suffix))
            print(("%i files (done)" % len(removed)))
            if options.loglevel >= 3:
                print(("\n".join(removed)))
            if options.dry_run:
                print(("\n".join(removed)))
if __name__ == "__main__":
    sys.exit(main())
