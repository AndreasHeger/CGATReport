#!/bin/env python

"""
sphinxreport-profile
====================

:command:`sphinxreport-profile` examines the log file and
computes some summary statistics on rendering times.

   sphinxreport-profile

The full list of command line options is listed by suppling :option:`-h/--help`
on the command line. The options are:

**-s/--section** choice
   Only examine performance of certain aspects of sphinxreport. Possible choices are
   ``tracker``, ``rst``, and ``renderer``.

**-t/--time** choice
   Report times either as ``milliseconds`` or ``seconds``.

.. note::

   All times are wall clock times.

"""

import sys, os, imp, cStringIO, re, types, glob, optparse, shutil, datetime
import collections

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from SphinxReport import Component

class Counter(object):
    '''
    
    This class stores the calls per source as calls can be made by
    different sources in any order.
    '''

    def __init__(self):
        self.durations = collections.defaultdict( list )
        self.started = collections.defaultdict( int )

    def add( self, started, dt, source = None ):
        if self.started[source] != 0 and not started:
            self.durations[source].append( dt - self.started[source] )
            self.started[source] = 0
        elif self.started[source] == 0 and started:
            self.started[source] = dt
        else:
            raise ValueError("inconsistent time points, %s, %s" % (self.started[source], started))

    def reset( self, source = None):
        '''reset last event.'''
        self.started[source] = None

    def getDuration( self ): 
        if self.durations:
            x = None
            for source, durations in self.durations.iteritems():
                if x == None: x = durations[0] 
                for y in durations[1:]: x += y
            return x
        else:
            return datetime.timedelta()

    def getCalls( self ): 
        return sum( [ len(x) for x in self.durations.values() ] )

    duration = property(getDuration)
    calls = property(getCalls)

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-s", "--section", dest="sections", type="choice", action="append",
                       choices=("tracker", "rst", "renderer"),
                       help="only examine certain sections [default=%default]" )

    parser.add_option( "-t", "--time", dest="time", type="choice",
                       choices=("seconds", "milliseconds" ),
                       help="time to show [default=%default]" )

    parser.set_defaults( sections = [],
                         time = "seconds" )

    (options, args) = parser.parse_args()

    rx = re.compile("^[0-9]+" )

    if options.sections:
        profile_sections = options.sections
    else:
        profile_sections = ("rst", "tracker", "renderer" )

    counts = {}
    for section in profile_sections:
        counts[section] = collections.defaultdict( Counter )

    rootpath = os.path.abspath(".")

    if len(args) == 1:
        infile = open( args[0] )
    else:
        infile = open(Component.LOGFILE )

    for line in infile:

        if not rx.match( line ): continue
        data = line[:-1].split()
        if len(data) < 5: continue
        date, time, level, source, action = data[:5]

        if action != "profile:": continue

        dt = datetime.datetime.strptime( " ".join( (date, time) ), "%Y-%m-%d %H:%M:%S,%f")

        try:
            started, section = data[5:7]
            point = re.sub( "object at .*>","", " ".join(data[7:]))
            if point.startswith("<"): point = point[1:]
            point = re.sub( rootpath, "", point )
        except (IndexError, ValueError):
            print data[5:]
            print "malformatted line in logfile: %s" % line 
            continue
        
        if section.endswith( ":" ): section = section[:-1]
        
        if source == "report_directive.run:": continue
        is_start = started == "started:"

        if source == "build.py:":
            if is_start:
                print "# reseting counts at", line,
                counts = {}
                for s in profile_sections:
                    counts[s] = collections.defaultdict( Counter )
            continue

        try:
            counts[section][point].add( is_start, dt, source )
        except ValueError:
            # if there are errors, there is no finish, reset counter

            if is_start: counts[section[:-1]][point].reset( source )
            try:
                counts[section[:-1]][point].add( is_start, dt, source )
            except ValueError:
                print "error in line: (is_start=%s), %s" % (is_start,line)
                raise

    if options.time == "milliseconds":
        f = lambda d: d.seconds + d.microseconds / 1000
    elif options.time == "seconds":
        f = lambda d: d.seconds + d.microseconds / 1000000

    for section in profile_sections:
        sys.stdout.write( "\t".join( ("section", "object", "ncalls", "duration", "percall") ) + "\n" )
        for objct, c in counts[section].iteritems():
            d = f(c.duration)
            if c.calls > 0:
                percall = "%6.3f" %( d / float(c.calls))
            else:
                percall = "na"
            sys.stdout.write( "\t".join( \
                    (map( str, \
                              (section, objct, 
                               c.calls,
                               d,
                               percall,
                               )))) + "\n" )
            
        sys.stdout.write( "\n" * 3 )

if __name__ == "__main__":
    sys.exit(main())
