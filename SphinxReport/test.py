#!/bin/env python

"""
sphinxreport-test
=================

:file:`sphinxreport-test` permits testing :class:`Trackers` and
:class:`Renderers` before using them in documents. The full list of
command line options is available using the :option:`-h/--help` command line
options.

There are three main usages of :command:`sphinxreport-test`:

Fine-tuning plots
-----------------

Given a :class:`Tracker` and :class:`Renderer`, sphinxreport-test
will call the :class:`Tracker` and supply it to the :class:`Renderer`::

   sphinxreport-test tracker renderer

Use this method to fine-tune plots. Additional options can be supplied
using the ``-o`` command line option. The script will output a template
restructured text snippet that can be directly inserted into a document.

Rendering a document
--------------------

With the ``-p/--page`` option, ``sphinxreport-test`` will create the restructured
text document as it is supplied to sphinx::

   sphinxreport-test --page=example.rst

This functionality is useful for debugging.

Testing trackers
----------------

Running sphinxreport-test without options::

   sphinxreport-test

will collect all :class:`Trackers` and will execute them.
Use this method to see if all :class:`Trackers` can access
their data sources.

"""


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
from SphinxReport.Transformer import *
from SphinxReport.report_directive import MAP_RENDERER, MAP_TRANSFORMER
import SphinxReport.report_directive
import SphinxReport.clean
from SphinxReport.Dispatcher import Dispatcher


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
    
    returns a tuple (code, tracker, module, flag).

    The flag indicates whether that tracker is derived from the 
    tracker base class. If False, that tracker will not be listed
    as an available tracker, though it might be specified at the
    command line.
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
            trackers.append( (name, obj, module_name, True) )
        elif isinstance(obj, (type, types.FunctionType)):
            trackers.append( (name, obj, module_name, False) )
        elif isinstance(obj, (type, types.LambdaType)):
            trackers.append( (name, obj, module_name, False) )

    return trackers

def run( name, t, kwargs ):
    
    print "%s: collecting data started" % name     
    t( **kwargs )
    print "%s: collecting data finished" % name     

def main():

    parser = optparse.OptionParser( version = "%prog version: $Id$", usage = USAGE )

    parser.add_option( "-t", "--tracker", dest="tracker", type="string",
                          help="tracker to use [default=%default]" )

    parser.add_option( "-p", "--page", dest="page", type="string",
                          help="render an rst page [default=%default]" )

    parser.add_option( "-a", "--tracks", dest="tracks", type="string",
                          help="tracks to use [default=%default]" )

    parser.add_option( "-m", "--transformer", dest="transformers", type="string", action="append",
                          help="add transformation [default=%default]" )

    parser.add_option( "-s", "--slices", dest="slices", type="string",
                          help="slices to use [default=%default]" )

    parser.add_option( "-r", "--renderer", dest="renderer", type="string",
                          help="renderer to use [default=%default]" )

    parser.add_option( "-f", "--force", dest="force", action="store_true",
                          help="force recomputation of data by deleting cached results [default=%default]" )

    parser.add_option( "-o", "--option", dest="options", type="string", action="append",
                       help="renderer options - supply as key=value pairs (without spaces). [default=%default]" )

    parser.add_option( "--no-print", dest="do_print", action="store_false",
                       help = "do not print an rst text element to create the displayed plots [default=%default]." )

    parser.add_option( "--no-show", dest="do_show", action="store_false",
                       help = "do not show a plot [default=%default]." )

    parser.set_defaults(
        tracker=None,
        transformers = [],
        tracks=None,
        slices=None,
        options = [],
        renderer = None,
        do_show = True,
        do_print = True,
        force = False,
        label = "GenericLabel",
        caption = "add caption here" )
    
    (options, args) = parser.parse_args()

    if len(args) == 2:
        options.tracker, options.renderer = args

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

    if options.renderer:
        try:
            renderer = MAP_RENDERER[options.renderer]
        except KeyError:
            print "could not find renderer '%s'. Available renderers:\n  %s" % \
                (options.renderer, "\n  ".join(sorted(MAP_RENDERER.keys())))
            sys.exit(1)
    else:
        renderer = Renderer

    transformers = []
    for transformer in options.transformers:
        try:
            transformers.append( MAP_TRANSFORMER[transformer]( *args, **kwargs) )
        except KeyError, msg:
            print "could not instantiate transformer '%s': %s.\nAvailable transformers:\n  %s" % \
                (transformer, msg, "\n  ".join(sorted(MAP_TRANSFORMER.keys())))
            sys.exit(1)

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

        available_trackers = set( [ x[0] for x in trackers if x[3] ] )
        if options.tracker not in available_trackers:
            print "unknown tracker '%s': possible trackers are\n  %s" % (options.tracker, "\n  ".join( sorted(available_trackers)) ) 
            sys.exit(1)

        for name, tracker, modulename, is_derived  in trackers:
            if name == options.tracker: break
        
        ## remove everything related to that tracker for a clean slate
        if options.force:
            removed = SphinxReport.clean.removeTracker( name )
            print "removed all data for tracker %s: %i files" % (name, len(removed))

        t = tracker()
        dispatcher = Dispatcher( t, renderer(t,**kwargs), transformers ) 
        ## needs to be resolved between renderer and dispatcher options
        result = dispatcher( **kwargs )
        
        #r = renderer( tracker() )

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
            if options.transformers:                                                                  
                params["options"] = ":transform: %s\n   %s" %\
                    (",".join(options.transformers), params["options"] )

            print RST_TEMPLATE % params
            print
            print "..Template ends"
        if result: 
            for r in result:
                print "title:", r.title
                for s in r:
                    print str(s)
        if options.do_show: plt.show()

    elif options.page:
        import build
        SphinxReport.report_directive.DEBUG = True
        SphinxReport.report_directive.FORCE = True

        blocks = build.rst_reader( open( options.page, "r") )
        for block in blocks:
            build.run( ( (options.page, block ),) )
            
    else:
        trackers = []
        for filename in glob.glob( "python/*.py" ):
            trackers.extend( [ x for x in getTrackers( filename ) if x[0] not in exclude ] )

        processes = []
        for name, tracker, modulename, is_derived in trackers:
            if not is_derived: continue
            obj = tracker()
            r = renderer( obj )
            p = Process( target = run, args= ( name,r,kwargs ) )
            processes.append( (name, p) )
            p.start()

        for name, p in processes:
            p.join()

if __name__ == "__main__":
    sys.exit(main())
