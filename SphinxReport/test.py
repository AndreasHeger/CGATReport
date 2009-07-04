#!/bin/env python
import sys, os, imp, cStringIO, re, types, glob, optparse

USAGE = """python %s [OPTIONS] [tracker renderer]

evaluate all Trackers in the python directory.

The script collects all Trackers in the 'python' directory
and evaluates them. The Trackers are evaluated in parallel
and thus allow a much faster data collection than through
sphinx.
"""

import matplotlib
import matplotlib.pyplot as plt

from SphinxReport.Tracker import Tracker
from SphinxReport.Renderer import *
from SphinxReport.report_directive import MAP_RENDERER

try:
    from multiprocessing import Process
except ImportError:
    from threading import Thread as Process

if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

RST_TEMPLATE = """.. _%(label)s:

.. report:: %(tracker)s
   :render: %(renderer)s
   %(options)s

   %(caption)s
"""

def getTrackers( fullpath ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """
    name, cls = os.path.splitext(fullpath)
    # remove leading '.'
    cls = cls[1:]
    module_name = os.path.basename(name)
    
    try:
        (file, pathname, description) = imp.find_module( module_name )
    except ImportError, msg:
        print "could not find module %s" % name
        raise

    if file == None: return []

    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    try:
        module = imp.load_module(name, file, pathname, description )
    except:
        raise
    finally:
        file.close()
        sys.stdout = stdout

    trackers = []

    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, (type, types.ClassType)) and \
                issubclass(obj, Tracker) and hasattr(obj, "__call__"):
            trackers.append( (name, obj, module_name) )
        elif isinstance(obj, (type, types.FunctionType)):
            trackers.append( (name, obj, module_name) )
        elif isinstance(obj, (type, types.LambdaType)):
            trackers.append( (name, obj, module_name) )

    return trackers

def run( name, t, kwargs ):
    
    print "%s: collecting data started" % name     
    t( **kwargs )
    print "%s: collecting data finished" % name     

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-t", "--tracker", dest="tracker", type="string",
                          help="tracker to use [default=%default]" )

    parser.add_option( "-a", "--tracks", dest="tracks", type="string",
                          help="tracks to use [default=%default]" )

    parser.add_option( "-s", "--slices", dest="slices", type="string",
                          help="slices to use [default=%default]" )

    parser.add_option( "-r", "--renderer", dest="renderer", type="string",
                          help="renderer to use [default=%default]" )

    parser.add_option( "-o", "--option", dest="options", type="string", action="append",
                       help="renderer options - supply as key=value pairs (without spaces). [default=%default]" )

    parser.add_option( "--no-print", dest="do_print", action="store_false",
                       help = "do not print an rst text element to create the displayed plots [default=%default]." )

    parser.add_option( "--no-show", dest="do_show", action="store_false",
                       help = "do not show a plot [default=%default]." )

    parser.set_defaults(
        tracker=None,
        tracks=None,
        slices=None,
        options = [],
        renderer = None,
        do_show = True,
        do_print = True,
        label = "GenericLabel",
        caption = "add caption here" )
    
    (options, args) = parser.parse_args()

    if len(args) == 2:
        options.tracker, options.renderer = args

    if options.renderer:
        try:
            renderer = MAP_RENDERER[options.renderer]
        except IndexError:
            raise IndexError("could not find renderer '%s'. Available are %s" % MAP_RENDERER.keys() )
    else:
        renderer = Renderer

    kwargs = {}
    for x in options.options:
        if "=" in x:
            data = x.split("=")
            key,val = [ y.strip() for y in (data[0], "=".join(data[1:])) ]
        else:
            key, val = x.strip(), None
        kwargs[key] = val
    
    if options.tracks: kwargs["tracks"] = options.tracks
    if options.slices: kwargs["slices"] = options.slices

    exclude = set( ("Tracker", 
                    "TrackerSQL", 
                    "returnLabeledData",
                    "returnMultipleColumnData",
                    "returnMultipleColumns",
                    "returnSingleColumn",
                    "returnSingleColumnData", 
                    "SQLError", 
                    "MultipleColumns", 
                    "MultipleColumnData", 
                    "LabeledData", 
                    "DataSimple", 
                    "Data"  ) )

    if options.tracker:

        trackers = []
        for filename in glob.glob( "python/*.py" ):
            trackers.extend( [ x for x in getTrackers( filename ) if x[0] not in exclude ] )

        available_trackers = set( [ x[0] for x in trackers ] )
        if options.tracker not in available_trackers:
            raise NameError( "unknown tracker '%s': possible trackers are\n %s" % (options.tracker, "\n".join( sorted(available_trackers)) ) )

        for name, tracker, modulename in trackers:
            if name == options.tracker: break

        r = renderer( tracker() )
        result = r( **kwargs)
        if options.do_print:                        
            options_rst = []
            for key,val in kwargs.items():
                if val == None:
                    options_rst.append(":%s:" % key )
                else:
                    options_rst.append(":%s: %s" % (key,val) )

            print "..Template start"
            print
            params = { "tracker" : "%s.%s" % (modulename,name),
                       "renderer" : options.renderer,
                       "label" : options.label,
                       "options": ("\n   ").join(options_rst),
                       "caption" : options.caption }
            print RST_TEMPLATE % params
            print
            print "..Template ends"
        if result: print "\n".join(result)
        if options.do_show: plt.show()

    else:
        for filename in glob.glob( "python/*.py" ):
            processes = []
            for name, tracker, modulename in trackers:
                obj = tracker()
                r = renderer( obj )
                p = Process( target = run, args= ( name,r,kwargs ) )
                processes.append( (name, p) )
                p.start()

            for name, p in processes:
                p.join()

if __name__ == "__main__":
    sys.exit(main())
