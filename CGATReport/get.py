#!/bin/env python

"""
cgatreport-get
================

:command:`cgatreport-get` queries the CGATReport cache
and retrieves data.

   cgatreport-get tracker

The full list of command line options is listed by suppling:option:`-h/--help`
on the command line.

The options are:

**-t/--tracker** tracker
:class:`Tracker` to use.

**-a/--tracks** tracks
   Tracks to display as a comma-separated list. If none are given, output all tracks.

**-s/--slices** slices
   Slices to display as a comma-separated list. If none are given, output all slices

**-v/--view**
   Do not ouput data, but display list of available tracks and slices.

**-g/--groupby** group by
   (track,slice)
   Group output either by:term:`track` or:term:`slice`.

**-f/--format** output format
   (tsv, csv)
   Output format. Available are:

   * ``tsv``: tab-separated values
   * ``csv``: comma-separated values

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

USAGE = """python %s [OPTIONS]

query the CGATReport cache.

""" % sys.argv[0]


from CGATReport import Utils
from CGATReport import Cache
from CGATReport import DataTree
from collections import OrderedDict as odict


def main():

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-v", "--verbose", dest="loglevel", type="int",
                      help="loglevel. The higher, the more output [default=%default]")

    parser.add_option("-i", "--view", dest="view", action="store_true",
                      help="view keys in cache [default=%default]")

    parser.add_option("-t", "--tracker", dest="tracker", type="string",
                      help="tracker to use [default=%default]")

    parser.add_option("-a", "--tracks", dest="tracks", type="string",
                      help="tracks to include [default=%default]")

    parser.add_option("-s", "--slices", dest="slices", type="string",
                      help="slices to include [default=%default]")

    parser.add_option("-g", "--groupby", dest="groupby", type="choice",
                      choices=("track", "slice", "all"),
                      help="groupby by track or slice [default=%default]")

    parser.add_option("-f", "--format", dest="format", type="choice",
                      choices=("tsv", "csv"),
                      help="output format [default=%default]")

    parser.set_defaults(
        loglevel=2,
        view=False,
        tracker=None,
        tracks=None,
        slices=None,
        groupby="slice",
        format="tsv",
    )

    (options, args) = parser.parse_args()

    if len(args) != 1 and options.tracker == None:
        print(USAGE)
        raise ValueError("please supply a tracker.""")

    if options.tracker:
        tracker = options.tracker
    else:
        tracker = args[0]

    cache = Cache.Cache(tracker, mode="r")

    if options.view:
        keys = [x.split("/") for x in list(cache.keys())]
        sys.stdout.write("# available tracks\n")
        sys.stdout.write("track\n%s" % "\n".join(set([x[0] for x in keys])))
        sys.stdout.write("\n")
        sys.stdout.write("# available slices\n")
        sys.stdout.write("slice\n%s" % "\n".join(set([x[1] for x in keys])))
        sys.stdout.write("\n")
        return

    data = DataTree.fromCache(cache,
                              tracks=options.tracks,
                              slices=options.slices,
                              groupby=options.groupby)

    table, row_headers, col_headers = DataTree.tree2table(data)

    if options.format in ("tsv", "csv"):
        if options.format == "tsv":
            sep = "\t"
        elif options.format == "csv":
            sep = ","
        sys.stdout.write(sep + sep.join(col_headers) + "\n")
        for h, row in zip(row_headers, table):
            sys.stdout.write("%s%s%s\n" % (h, sep, sep.join(row)))

if __name__ == "__main__":
    sys.exit(main())
