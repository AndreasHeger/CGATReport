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
   :term:`tracker` to use.

**-r/--renderer** renderer
   :term:`renderer` to use.

**-f/--force** 
   force update of a :class:`Tracker`. Removes all data from cache.

**-m/--transformer** transformer
   :class:`Transformer` to use. Several transformers can be applied via multiple **-m** options.

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

**--no-show**
   Do not show plot. Use this to just display the tracks/slices that will be generated.

**-w/--path** path
   Path with trackers. By default, :term:`trackers` are searched in the directory :file`trackers` 
   within the current directory.

If no command line arguments are given all :term:`trackers` are build in parallel. 

Usage
-----

There are three main usages of :command:`sphinxreport-test`:

Fine-tuning plots
+++++++++++++++++

Given a :class:`Tracker` and :class:`Renderer`, sphinxreport-test
will call the :class:`Tracker` and supply it to the :class:`Renderer`::

   sphinxreport-test tracker renderer

Use this method to fine-tune plots. Additional options can be supplied
using the ``-o`` command line option. The script will output a template
restructured text snippet that can be directly inserted into a document.

Rendering a document
++++++++++++++++++++

With the ``-p/--page`` option, ``sphinxreport-test`` will create the restructured
text document as it is supplied to sphinx::

   sphinxreport-test --page=example.rst

This functionality is useful for debugging.

Testing trackers
++++++++++++++++

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

from SphinxReport.Component import *
from SphinxReport.Tracker import Tracker
from SphinxReport import Utils

import SphinxReport.clean
from SphinxReport.Dispatcher import Dispatcher

try:
    from multiprocessing import Process
except ImportError:
    from threading import Thread as Process

# import conf.py
if os.path.exists("conf.py"):
    try:
        execfile( "conf.py" )
    except ValueError:
        pass

# set default directory where trackers can be found
TRACKERDIR = "trackers"
if "docsdir" in locals():
    TRACKERDIR = os.path.join( docsdir, "trackers" )

RST_TEMPLATE = """.. _%(label)s:

.. report:: %(tracker)s
   :render: %(renderer)s
   %(options)s

   %(caption)s
"""

def getTrackers( fullpath ):
    """retrieve a tracker and its associated code.
    
    The tracker is not instantiated.

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

    parser.add_option( "-w", "--path", dest="dir_trackers", type="string",
                          help="path to trackers [default=%default]" )

    parser.add_option( "-f", "--force", dest="force", action="store_true",
                          help="force recomputation of data by deleting cached results [default=%default]" )

    parser.add_option( "-o", "--option", dest="options", type="string", action="append",
                       help="renderer options - supply as key=value pairs (without spaces). [default=%default]" )

    parser.add_option( "--no-print", dest="do_print", action="store_false",
                       help = "do not print an rst text element to create the displayed plots [default=%default]." )

    parser.add_option( "--no-show", dest="do_show", action="store_false",
                       help = "do not show a plot [default=%default]." )

    parser.add_option( "--hardcopy", dest="hardcopy", type="string",
                       help = "output images of plots. The parameter should contain one or more %s "
                              " The suffix determines the type of plot. "
                              " [default=%default]." )

    parser.set_defaults(
        loglevel = 1,
        tracker=None,
        transformers = [],
        tracks=None,
        slices=None,
        options = [],
        renderer = None,
        do_show = True,
        do_print = True,
        force = False,
        dir_trackers = TRACKERDIR,
        label = "GenericLabel",
        caption = "add caption here",
        dpi = 100 )
    
    (options, args) = parser.parse_args()

    if len(args) == 2:
        options.tracker, options.renderer = args
        
    # configure options
    options.dir_trackers = os.path.abspath( os.path.expanduser( options.dir_trackers ) )
    if not os.path.exists( options.dir_trackers ):
        raise IOError("directory %s does not exist" % options.dir_trackers )

    sys.path.insert( 0, options.dir_trackers )

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

    option_map = getOptionMap()
    renderer_options = Utils.selectAndDeleteOptions( kwargs, option_map["render"])
    transformer_options = Utils.selectAndDeleteOptions( kwargs, option_map["transform"])
    display_options = Utils.selectAndDeleteOptions( kwargs, option_map["display"])

    renderer = Utils.getRenderer( options.renderer, renderer_options )

    transformers = Utils.getTransformers( options.transformers, transformer_options )

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
            modulename = os.path.basename( filename )
            trackers.extend( [ x for x in getTrackers( modulename ) if x[0] not in exclude ] )
        
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
        if is_derived: t = tracker( **kwargs )
        # but not functions
        else: t = tracker

        dispatcher = Dispatcher( t, renderer, transformers ) 

        ## needs to be resolved between renderer and dispatcher options
        result = dispatcher( **kwargs )

        if options.do_print:                        
            options_rst = []
            for key,val in kwargs.items() + renderer_options.items() + transformer_options.items() + display_options.items():
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
                    
        if options.hardcopy:
            
            fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()
            # create all the images
            for figman in fig_managers:
                # create all images
                figid = figman.num
                outfile = re.sub( "%s", str(figid), options.hardcopy)
                figman.canvas.figure.savefig( outfile, dpi=options.dpi )

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
        
        if not os.path.exists( options.page ):
            raise IOError( "page %s does not exist" % options.page)

        options.num_jobs = 1

        build.buildPlots( [ options.page, ], options, [], os.path.dirname( options.page ) )

        if options.do_show: 
            if options.renderer.startswith("r-"):
                print "press Ctrl-c to stop"
                while 1: pass
            
            elif _pylab_helpers.Gcf.get_all_fig_managers() > 0:
                plt.show()

    else:
        raise ValueError("please specify either a tracker (-t/--tracker) or a page (-p/--page) to test")
            
if __name__ == "__main__":
    sys.exit(main())

