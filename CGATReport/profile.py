#!/bin/env python

"""
cgatreport-profile
====================

:command:`cgatreport-profile` examines the log file and
computes some summary statistics on rendering times.

   cgatreport-profile

The full list of command line options is listed by suppling:option:`-h/--help`
on the command line. The options are:

**-s/--section** choice
   Only examine performance of certain aspects of cgatreport. Possible choices are
   ``tracker``, ``rst``, and ``renderer``.

**-t/--time** choice
   Report times either as ``milliseconds`` or ``seconds``.

.. note::

   All times are wall clock times.

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
import datetime
import logging
import collections

USAGE = """python %s [OPTIONS] target

clean all data according to target.

Targets can contain wild cards.

""" % sys.argv[0]

from CGATReport import Component


class Counter(object):

    '''

    This class stores the calls per source as calls can be made by
    different sources in any order.
    '''

    def __init__(self):
        self._durations = collections.defaultdict(list)
        self._started = collections.defaultdict(int)
        self._calls = collections.defaultdict(int)

    def add(self, started, dt, source=None):
        if self._started[source] != 0 and not started:
            self._durations[source].append(dt - self._started[source])
            self._started[source] = 0
        elif self._started[source] == 0 and started:
            self._calls[source] += 1
            self._started[source] = dt
        else:
            raise ValueError("inconsistent time points, has_started=%s, is_started=%s" % (
                self._started[source], started))

    def reset(self, source=None):
        '''reset last event.'''
        self._started[source] = None
        self._calls[source] = 0

    def getDuration(self):
        if self._durations:
            x = None
            for source, durations in list(self._durations.items()):
                if x == None:
                    x = durations[0]
                for y in durations[1:]:
                    x += y
            return x
        else:
            return datetime.timedelta()

    def getCalls(self):
        return sum(self._calls.values())

    def getRunning(self):
        '''get numbers of tasks unfinished or still running.'''
        return len([x for x, y in list(self._started.items()) if y != 0])

    duration = property(getDuration)
    calls = property(getCalls)
    running = property(getRunning)


def main(argv=None):

    if argv == None:
        argv = sys.argv

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-s", "--section", dest="sections", type="choice", action="append",
                      choices=("tracker", "rst", "renderer"),
                      help="only examine certain sections [default=%default]")

    parser.add_option("-t", "--time", dest="time", type="choice",
                      choices=("seconds", "milliseconds"),
                      help="time to show [default=%default]")

    parser.add_option("-f", "--filter", dest="filter", type="choice",
                      choices=("unfinished", "running", "completed", "all"),
                      help="apply filter to output [default=%default]")

    parser.set_defaults(sections=[],
                        filter="all",
                        time="seconds")

    (options, args) = parser.parse_args()

    rx = re.compile("^[0-9]+")

    if options.sections:
        profile_sections = options.sections
    else:
        profile_sections = ("rst", "tracker", "renderer", "transformer")

    counts = {}
    for section in profile_sections:
        counts[section] = collections.defaultdict(Counter)

    rootpath = os.path.abspath(".")

    if len(args) == 1:
        infile = open(args[0])
    else:
        infile = open(Component.LOGFILE)

    for line in infile:
        if not rx.match(line):
            continue
        data = line[:-1].split()
        if len(data) < 5:
            continue
        date, time, level, source, action = data[:5]

        if action != "profile:":
            continue

        dt = datetime.datetime.strptime(
            " ".join((date, time)), "%Y-%m-%d %H:%M:%S,%f")

        try:
            started, section = data[5:7]
            point = re.sub("object at .*>", "", " ".join(data[7:]))
            if point.startswith("<"):
                point = point[1:]
            point = re.sub(rootpath, "", point)
        except (IndexError, ValueError):
            print((data[5:]))
            print(("malformatted line in logfile: %s" % line))
            continue

        if section.endswith(":"):
            section = section[:-1]

        if source == "report_directive.run:":
            continue
        is_start = started == "started:"

        if source == "build.py:":
            if is_start:
                logging.info("resetting counts at line=%s" % line[:-1])
                counts = {}
                for s in profile_sections:
                    counts[s] = collections.defaultdict(Counter)
            continue

        try:
            counts[section][point].add(is_start, dt, source)
        except ValueError as msg:
            # if there are errors, there is no finish, reset counter
            if is_start:
                counts[section][point].reset(source)
            try:
                counts[section][point].add(is_start, dt, source)
            except ValueError as msg:
                logging.warn("%s: line=%s" % (msg, line))
            except KeyError as msg:
                print(data)
                print(("error in line: (is_start=%s), msg='%s', %s" %
                      (is_start, msg, line)))

    if options.time == "milliseconds":
        f = lambda d: d.seconds + d.microseconds / 1000
    elif options.time == "seconds":
        f = lambda d: d.seconds + d.microseconds / 1000000

    for section in profile_sections:
        sys.stdout.write("\t".join(
            ("section", "object", "ncalls", "duration", "percall", "running")) + "\n")

        running = []
        for objct, c in list(counts[section].items()):

            # apply filters
            if options.filter in ("unfinished", "running") and c.running == 0:
                continue

            d = f(c.duration)
            if c.calls > 0:
                percall = "%6.3f" % (d / float(c.calls))
            else:
                percall = "na"

            sys.stdout.write("\t".join(
                (list(map(str,
                          (section, objct,
                           c.calls,
                           d,
                           percall,
                           c.running,
                           ))))) + "\n")

            running.extend([x for x, y in list(c._started.items()) if y != 0])

        print("running")
        print(("\n".join(map(str, running))))
        sys.stdout.write("\n" * 3)

if __name__ == "__main__":
    sys.exit(main())
