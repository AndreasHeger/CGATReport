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

import sys, os, imp, cStringIO, re, types, glob, optparse, shutil, datetime
import collections

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from SphinxReport import Reporter

class Counter(object):
    def __init__(self):
        self.durations = []
        self.started = None

    def add( self, started, dt ):
        if self.started != None and not started:
            self.durations.append( dt - self.started )
            self.started = None
        elif self.started == None and started:
            self.started = dt
        else:
            raise ValueError("inconsistent time points, %s, %s" % (self.started, started))

    def reset( self ):
        '''reset last event.'''
        self.started = None

    def getDuration( self ): 
        if self.durations:
            x = self.durations[0] 
            for y in self.durations[1:]: x += y
            return x
        else:
            return datetime.timedelta()

    def getCalls( self ): return len(self.durations)

    duration = property(getDuration)
    calls = property(getCalls)

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

    sections = ("rst", "tracker", "renderer" )

    counts = {}
    for section in sections:
        counts[section] = collections.defaultdict( Counter )

    for line in open(Reporter.LOGFILE ):

        if not rx.match( line ): continue
        data = line[:-1].split()
        if len(data) < 5: continue
        date, time, level, source, action = data[:5]

        if action != "profile:": continue

        dt = datetime.datetime.strptime( " ".join( (date, time) ), "%Y-%m-%d %H:%M:%S,%f")

        try:
            started, section = data[5:7]
            point = re.sub( "object at .*>","", " ".join(data[7:]))
        except (IndexError, ValueError):
            print data[5:]
            print "malformatted line in logfile: %s" % line 
            continue
        
        if section == "renderer": section += ":"
        
        if source == "report_directive.run:": continue

        is_start = started == "started:"
        try:
            counts[section[:-1]][point].add( is_start, dt )
        except ValueError:
            # if there are errors, there is no finish, reset counter
            if is_start: counts[section[:-1]][point].reset()
            counts[section[:-1]][point].add( is_start, dt )
            

    for section in sections:
        sys.stdout.write( "\t".join( ("section", "object", "ncalls", "duration", "percall") ) + "\n" )
        for objct, c in counts[section].iteritems():
            d = c.duration
            dmilli = d.seconds * 1000 + d.microseconds / 1000
            if c.calls > 0:
                percall = "%6.3f" %( dmilli / float(c.calls))
            else:
                percall = "na"
            sys.stdout.write( "\t".join( \
                    (map( str, \
                              (section, objct, 
                               c.calls,
                               dmilli,
                               percall,
                               )))) + "\n" )
            
        sys.stdout.write( "\n" * 3 )

if __name__ == "__main__":
    sys.exit(main())
