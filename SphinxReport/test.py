#! /bin/env python

"""
sphinxreport-test
=================

:file:`sphinxreport-test` permits testing :class:`Trackers` and
:class:`Renderers` before using them in documents. The full list of
command line options is available using the :option:`-h/--help` command line
options.

The options are:

**-t/--tracker** tracker
   :class:`Tracker` to use.

**-r/--renderer** renderer
   :class:`Renderer` to use.

**-f/--force** 
   force update of :class:`Tracker`a.

**-m/--transformer** transformer
   :class:`Transformer` to use.

**-a/--tracks** tracks
   Tracks to display as a comma-separated list.

**-s/--slices** slices
   Slices to display as a comma-separated list.

**-o/--option** option
   Options for the renderer/transformer. These correspond to options
   within restructured text directives, but supplied as key=value pairs (without spaces). 
   For example: ``:width: 300`` will become ``-o width=300``. Several **-o** options can
   be supplied on the command line.

**--no-print**
   Do not print an rst text template corresponding to the displayed plots.

**--no-plot**
   Do not plot.

If no command line arguments are given all :class:`Tracker` are build in parallel. 

Usage
-----

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
from matplotlib import _pylab_helpers

from rpy import r as R

from SphinxReport.Component import *
from SphinxReport.Tracker import Tracker
# from SphinxReport.Renderer import *
# from SphinxReport.Transformer import *
from SphinxReport import Utils

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
    module, pathname = Utils.getModule( name )

    trackers = []

    for name in dir(module):
        obj = getattr(module, name)
        try:
            if Utils.isClass( obj ):
                trackers.append( (name, obj, module_name, True) )
            else:
                trackers.append( (name, obj, module_name, False) )
        except ValueError:
            pass
        
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

    parser.add_option( "-w", "--path", dest="path", type="string",
                          help="path to trackers [default=%default]" )

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
        dir_trackers = "python",
        label = "GenericLabel",
        caption = "add caption here" )
    
    (options, args) = parser.parse_args()

    if len(args) == 2:
        options.tracker, options.renderer = args

    # test plugins
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

    if options.renderer == None: options.renderer = "table"

    kwargs = Utils.updateOptions( kwargs )

    renderer = Utils.getRenderer( options.renderer, **kwargs )

    transformers = Utils.getTransformers( options.transformers, **kwargs )

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
        for filename in glob.glob( os.path.join( options.dir_trackers, "*.py" )):
            trackers.extend( [ x for x in getTrackers( filename ) if x[0] not in exclude ] )
        
        for name, tracker, modulename, is_derived  in trackers:
            if name == options.tracker: break
        else:
            available_trackers = set( [ x[0] for x in trackers if x[3] ] )
            print "unknown tracker '%s': possible trackers are\n  %s" % (options.tracker, "\n  ".join( sorted(available_trackers)) ) 
            print "(the list above does not contain functions)."
            sys.exit(1)

        ## remove everything related to that tracker for a clean slate
        if options.force:
            removed = SphinxReport.clean.removeTracker( name )
            print "removed all data for tracker %s: %i files" % (name, len(removed))

        # instantiate functors
        if is_derived: t = tracker()
        # but not functions
        else: t = tracker

        dispatcher = Dispatcher( t, renderer, transformers ) 

        ## needs to be resolved between renderer and dispatcher options
        result = dispatcher( **kwargs )

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

        if options.do_show: 
            if options.renderer.startswith("r-"):
                print "press Ctrl-c to stop"
                while 1: pass
            
            elif _pylab_helpers.Gcf.get_all_fig_managers() > 0:
                plt.show()

    elif options.page:
        import build
        SphinxReport.report_directive.DEBUG = True
        SphinxReport.report_directive.FORCE = True

        blocks = build.rst_reader( open( options.page, "r") )
        for block in blocks:
            build.run( ( (options.page, block ),) )
            
if __name__ == "__main__":
    sys.exit(main())

