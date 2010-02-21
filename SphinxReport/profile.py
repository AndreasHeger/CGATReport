#!/bin/env python

"""
sphinxreport-profile
====================

:command:`sphinxreport-profile` examines the log file and
computes some summary statistics on rendering times.

   sphinxreport-profile

The full list of command line options is listed by suppling :option:`-h/--help`
on the command line.


.. note::

   All times are wall clock times.

"""

import sys, os, imp, cStringIO, re, types, glob, optparse, shutil

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from SphinxReport import Reporter

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

    rx = re.compile("^[0-9]+" )

    for line in open(Reporter.LOGFILE ):

        if not rx.match( line ): continue
        data = line[:-1].split()
        if len(data) < 4: continue
        date, time, level, objct = data[0:4]
        msg = " ".join(data[4:])
        print date, time, level, objct

if __name__ == "__main__":
    sys.exit(main())
