#!/bin/env python
import sys
import re
import glob
import os
import optparse

from CGATReport import Utils

USAGE = """%s [OPTIONS]

set up an new cgatreport in the current directory.
""" % sys.argv[0]


def main(argv=None):

    if argv is None:
        argv = sys.argv

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-d", "--dest", dest="destination", type="string",
                      help="destination directory.")

    parser.set_defaults(
        destination=".",
    )

    (options, args) = parser.parse_args()

    dest = options.destination

    # create directories
    for d in ("",
              "_templates",
              "cgat",
              "cgat/static",
              "trackers",
              "templates"):
        dd = os.path.join(dest, d)
        if not os.path.exists(dd):
            os.makedirs(dd)

    # copy files
    def copy(src, dst):
        fn = os.path.join(dest, dst, os.path.basename(src))
        if os.path.exists(fn):
            raise OSError("file %s already exists - not overwriting." % fn)

        outfile = open(fn, "w")
        x = Utils.get_data("CGATReport", "templates/%s" % src)
        if len(x) == 0:
            raise ValueError('file %s is empty' % src)
        outfile.write(x)
        outfile.close()

    for f in ("Makefile",
              "server.py",
              "cgatreport.ini",
              "conf.py",
              "contents.rst"):
        copy(f, "")

    # for f in ("indexsidebar.html",
    #           "layout.html",
    #           "search.html"):
    #     copy(f, "_templates")

    # for f in ("data_table.html",):
    #     copy(f, "templates")

    for f in ("theme.conf", "layout.html"):
        copy(f, "cgat")

    for f in ("cgat.css_t",
              "js/sorttable.js",
              "js/jquery.dataTables.min.js",
              "js/notebook.js",
              "js/jssor.js",
              "js/jssor.slider.js"):
        copy(f, os.path.join("cgat", "static"))

    for f in ("Trackers.py", ):
        copy(f, "trackers")

    print("""
Welcome to CGATReport.

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
