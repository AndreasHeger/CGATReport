#!/bin/env python
import sys, re, os
import optparse

from SphinxReport import Utils

USAGE="""%s [OPTIONS]

set up an new sphinxreport in the current directory.
""" % sys.argv[0]

def main(argv = None):

    if argv == None: argv = sys.argv

    parser = optparse.OptionParser(version = "%prog version: $Id$", usage = USAGE)

    parser.add_option("-d", "--dest", dest="destination", type="string",
                      help="destination directory.")


    parser.set_defaults(
        destination = ".",
        )

    (options, args) = parser.parse_args()

    dest = options.destination

    # create directories
    for d in ("", "_templates", "labbook", "labbook/static", "analysis", "pipeline", "trackers", "templates"):
        dd = os.path.join(dest, d)
        if not os.path.exists(dd): os.makedirs(dd)

    # copy files
    def copy(src, dst):
        fn = os.path.join(dest, dst, src)
        if os.path.exists(fn):
            raise OSError("file %s already exists - not overwriting." % fn)

        outfile = open(fn, "w")
        x = Utils.get_data("SphinxReport", "templates/%s" % src)
        if len(x) == 0:
            raise ValueError('file %s is empty' % src)
        outfile.write(x)
        outfile.close()

    for f in ("Makefile",
              "server.py",
              "sphinxreport.ini",
              "conf.py",
              "analysis.rst",
              "contents.rst",
              "pipeline.rst",
              "usage.rst"):
        copy(f, "")

    for f in ("gallery.html",
              "index.html",
              "indexsidebar.html",
              "layout.html",
              "search.html"):
        copy(f, "_templates")

    for f in ("data_table.html",):
        copy(f, "templates")

    for f in ("Discussion.rst",
              "Introduction.rst",
              "Methods.rst",
              "Results.rst"):
        copy(f, "analysis")

    for f in ("PipelineTest.rst",):
        copy(f, "pipeline")

    for f in ("theme.conf",):
        copy(f, "labbook")

    for f in ("labbook.css",):
        copy(f, os.path.join("labbook", "static"))

    for f in ("Trackers.py", "Trackers.rst"):
        copy(f, "trackers")


    print("""
Welcome to SphinxReport.

All files have been successfully copied to `%(dest)s`. In order to build the
report, go to `%(dest)s`

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

""" % locals())


if __name__ == "__main__":
    sys.exit(main())
