#! /bin/env python

"""cgatreport-test
=================

:file:`cgatreport-test` permits testing:class:`Trackers` and
:class:`Renderers` before using them in documents. The full list of
command line options is available using the:option:`-h/--help` command line
options.

The options are:

**-t/--tracker** tracker
:term:`tracker` to use.

**-r/--renderer** renderer
:term:`renderer` to use.

**-f/--force**
   force update of a:class:`Tracker`. Removes all data from cache.

**-m/--transformer** transformer
   :class:`Transformer` to use. Several transformers can be applied
   via multiple **-m** options.

**-a/--tracks** tracks
   Tracks to display as a comma-separated list.

**-s/--slices** slices
   Slices to display as a comma-separated list.

**-o/--option** option
   Options for the renderer/transformer. These correspond to options
   within restructured text directives, but supplied as key=value
   pairs (without spaces).  For example: ``:width: 300`` will become
   ``-o width=300``. Several **-o** options can be supplied on the
   command line.

**--no-print**
   Do not print an rst text template corresponding to the displayed plots.

**--no-show**
   Do not show plot. Use this to just display the tracks/slices that
   will be generated.

**-w/--path** path
   Path with trackers. By default,:term:`trackers` are searched in the
   directory:file`trackers` within the current directory.

**-i/--interactive**
   Start python interpreter.

If no command line arguments are given all:term:`trackers` are build
in parallel.

Usage
-----

There are three main usages of:command:`cgatreport-test`:

Fine-tuning plots
+++++++++++++++++

Given a:class:`Tracker` and:class:`Renderer`, cgatreport-test
will call the:class:`Tracker` and supply it to the:class:`Renderer`::

   cgatreport-test tracker renderer

Use this method to fine-tune plots. Additional options can be supplied
using the ``-o`` command line option. The script will output a template
restructured text snippet that can be directly inserted into a document.

Rendering a document
++++++++++++++++++++

With the ``-p/--page`` option, ``cgatreport-test`` will create the
restructured text document as it is supplied to sphinx::

   cgatreport-test --page=example.rst

This functionality is useful for debugging.

Testing trackers
++++++++++++++++

Running cgatreport-test without options::

   cgatreport-test

will collect all:class:`Trackers` and will execute them.
Use this method to see if all:class:`Trackers` can access
their data sources.

"""
import sys
import os
import re
import glob
import optparse
import tempfile
import logging
import code

import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers

from CGATReport import Utils
from CGATReport import Component

import CGATReport.clean
from CGATReport.Dispatcher import Dispatcher
from CGATReport.Component import getOptionMap


# import conf.py
if os.path.exists("conf.py"):
    try:
        exec(compile(open("conf.py").read(), "conf.py", 'exec'))
    except ValueError:
        pass

# set default directory where trackers can be found
TRACKERDIR = "trackers"
if "docsdir" in locals():
    TRACKERDIR = os.path.join(docsdir, "trackers")

RST_TEMPLATE = """.. report:: %(tracker)s
   :render: %(renderer)s
   %(options)s

   %(caption)s
"""


def getTrackers(fullpath):
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
    module, pathname = Utils.getModule(name)
    trackers = []

    for name in dir(module):
        obj = getattr(module, name)

        try:
            if Utils.isClass(obj):
                trackers.append((name, obj, module_name, True))
            else:
                trackers.append((name, obj, module_name, False))
        except ValueError:
            pass

    return trackers


def writeRST(outfile, options, kwargs,
             renderer_options, transformer_options,
             display_options,
             modulename, name):
    '''write RST snippet to outfile to be include in a cgatreport document
    '''

    options_rst = []

    for key, val in list(kwargs.items()) +\
            list(renderer_options.items()) +\
            list(transformer_options.items()) +\
            list(display_options.items()):

        if val is None:
            options_rst.append(":%s:" % key)
        else:
            options_rst.append(":%s: %s" % (key, val))

    params = {"tracker": "%s.%s" % (modulename, name),
              "renderer": options.renderer,
              "options": ("\n   ").join(options_rst),
              "caption": options.caption}
    if options.transformers:
        params["options"] = ":transform: %s\n   %s" %\
            (",".join(options.transformers), params["options"])

    outfile.write(RST_TEMPLATE % params)


def writeNotebook(outfile, options, kwargs,
                  renderer_options,
                  transformer_options,
                  display_options,
                  modulename, name):
    '''write a snippet to paste with the ipython notebook.
    '''

    cmd_options = [
        'do_print = False',
        'tracker="%s"' % options.tracker,
        'renderer="%s"' % options.renderer,
        'trackerdir="%s"' % options.trackerdir,
        'workdir="%s"' % os.getcwd()]

    for key, val in list(kwargs.items()) +\
            list(renderer_options.items()) +\
            list(transformer_options.items()):
        if val is None:
            cmd_options.append("%s" % key)
        else:
            if Utils.isString(val):
                cmd_options.append('%s="%s"' % (key, val))
            else:
                cmd_options.append('%s=%s' % (key, val))
    if options.transformers:
        cmd_options.append(
            "transformer=['%s']" % "','".join(options.transformers))

    # no module name in tracker
    params = {"tracker": "%s" % (name),
              "options": ",\n".join(cmd_options)}

    outfile.write(Utils.NOTEBOOK_TEXT_TEMPLATE % params)


def run(name, t, kwargs):

    print("%s: collecting data started" % name)
    t(**kwargs)
    print("%s: collecting data finished" % name)


def main(argv=None, **kwargs):
    '''main function for test.py.

    Long-form of command line arguments can also be supplied as kwargs.

    If argv is not None, command line parsing will be performed.
    '''
    logger = Component.get_logger()

    parser = optparse.OptionParser(version="%prog version: $Id$",
                                   usage=globals()["__doc__"])

    parser.add_option("-t", "--tracker", dest="tracker", type="string",
                      help="tracker to use [default=%default]")

    parser.add_option("-p", "--page", dest="page", type="string",
                      help="render an rst page [default=%default]")

    parser.add_option("-a", "--tracks", dest="tracks", type="string",
                      help="tracks to use [default=%default]")

    parser.add_option("-m", "--transformer", dest="transformers",
                      type="string", action="append",
                      help="add transformation [default=%default]")

    parser.add_option("-s", "--slices", dest="slices", type="string",
                      help="slices to use [default=%default]")

    parser.add_option("-r", "--renderer", dest="renderer", type="string",
                      help="renderer to use [default=%default]")

    parser.add_option("-w", "--path", "--trackerdir",
                      dest="trackerdir", type="string",
                      help="path to trackers [default=%default]")

    parser.add_option("-f", "--force", dest="force", action="store_true",
                      help="force recomputation of data by deleting cached "
                      "results [default=%default]")

    parser.add_option("-o", "--option", dest="options", type="string",
                      action="append",
                      help="renderer options - supply as key=value pairs "
                      "(without spaces). [default=%default]")

    parser.add_option("-l", "--language", dest="language", type="choice",
                      choices=("rst", "notebook"),
                      help="output language for snippet. Use ``rst`` "
                      "to create a snippet to paste "
                      "into a cgatreport document. Use ``notebook`` to "
                      "create a snippet to paste "
                      "into an ipython notebook [default=%default]")

    parser.add_option("--no-print", dest="do_print", action="store_false",
                      help="do not print an rst text element to create "
                      "the displayed plots [default=%default].")

    parser.add_option("--no-show", dest="do_show", action="store_false",
                      help="do not show a plot [default=%default].")

    parser.add_option("--layout", dest="layout", type="string",
                      help="output rst with layout [default=%default].")

    parser.add_option("-i", "--start-interpreter", dest="start_interpreter",
                      action="store_true",
                      help="do not render, but start python interpreter "
                      "[default=%default].")

    parser.add_option("-I", "--ii", "--start-ipython", dest="start_ipython",
                      action="store_true",
                      help="do not render, start ipython interpreter "
                      "[default=%default].")

    parser.add_option(
        "--workdir", dest="workdir", type="string",
        help="working directory - change to this directory "
        "before executing "
        "[default=%default]")

    parser.add_option(
        "--hardcopy", dest="hardcopy", type="string",
        help="output images of plots. The parameter should "
        "contain one or more %s "
        "The suffix determines the type of plot. "
        "[default=%default].")

    parser.set_defaults(
        loglevel=1,
        tracker=None,
        transformers=[],
        tracks=None,
        slices=None,
        options=[],
        renderer="table",
        do_show=True,
        do_print=True,
        force=False,
        trackerdir=TRACKERDIR,
        caption="add caption here",
        start_interpreter=False,
        start_ipython=False,
        language="rst",
        workdir=None,
        layout=None,
        dpi=100)

    if argv is None and len(kwargs) == 0:
        argv = sys.argv

    if argv:
        (options, args) = parser.parse_args(argv)

        if len(args) == 2:
            options.tracker, options.renderer = args

    else:
        (options, args) = parser.parse_args([])

        ######################################################
        # set keyword arguments as options
        for keyword, value in kwargs.items():
            if hasattr(options, keyword):
                setattr(options, keyword, value)
                del kwargs[keyword]

        # change some kwarguments
        if options.transformers:
            for keyword, value in kwargs.items():
                if keyword.startswith("tf"):
                    kwargs["tf-{}".format(keyword[2:])] = value

    if options.workdir is not None:
        savedir = os.getcwd()
        os.chdir(options.workdir)
    else:
        savedir = None

    Utils.update_parameters(sorted(glob.glob("*.ini")))

    ######################################################
    # configure options
    options.trackerdir = os.path.abspath(
        os.path.expanduser(options.trackerdir))
    if os.path.exists(options.trackerdir):
        sys.path.insert(0, options.trackerdir)
    else:
        logger.warn("directory %s does not exist" % options.trackerdir)

    ######################################################
    # test plugins
    for x in options.options:
        if "=" in x:
            data = x.split("=")
            key, val = [y.strip() for y in (data[0], "=".join(data[1:]))]
        else:
            key, val = x.strip(), None
        kwargs[key] = val

    if options.tracks:
        kwargs["tracks"] = options.tracks
    if options.slices:
        kwargs["slices"] = options.slices

    kwargs = Utils.updateOptions(kwargs)

    option_map = getOptionMap()
    renderer_options = Utils.selectAndDeleteOptions(
        kwargs, option_map["render"])
    transformer_options = Utils.selectAndDeleteOptions(
        kwargs, option_map["transform"])
    display_options = Utils.selectAndDeleteOptions(
        kwargs, option_map["display"])

    ######################################################
    # decide whether to render or not
    if options.renderer == "none" or options.start_interpreter or \
       options.start_ipython or options.language == "notebook":
        renderer = None
    else:
        renderer = Utils.getRenderer(options.renderer, renderer_options)

    transformers = Utils.getTransformers(
        options.transformers, transformer_options)

    exclude = set(("Tracker",
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
                   "Data"))

    ######################################################
    # build from tracker
    if options.tracker:

        if "." in options.tracker:
            parts = options.tracker.split(".")
            tracker_modulename = ".".join(parts[:-1])
            tracker_name = parts[-1]
        else:
            tracker_modulename = None
            tracker_name = options.tracker

        try:
            _code, tracker, tracker_path = Utils.makeTracker(
                options.tracker, (), kwargs)
        except ImportError:
            # try to find class in module
            trackers = []

            for filename in glob.glob(
                    os.path.join(options.trackerdir, "*.py")):
                modulename = os.path.basename(filename)
                trackers.extend(
                    [x for x in getTrackers(modulename)
                     if x[0] not in exclude])

            for name, tracker_class, modulename, is_derived in trackers:
                if name == tracker_name:
                    if tracker_modulename is not None:
                        if modulename == tracker_modulename:
                            break
                    else:
                        tracker_modulename = modulename
                        break
            else:
                available_trackers = set([x[0] for x in trackers if x[3]])
                print(
                    "unknown tracker '%s': possible trackers are\n  %s" %
                    (options.tracker, "\n  ".join(sorted(available_trackers))))
                print(
                    "(the list above does not contain functions).")
                sys.exit(1)

            # instantiate functors
            if is_derived:
                tracker = tracker_class(**kwargs)
            #  but not functions
            else:
                tracker = tracker_class

        # remove everything related to that tracker for a clean slate
        if options.force:
            removed = CGATReport.clean.removeTracker(tracker_name)
            print("removed all data for tracker %s: %i files" %
                  (tracker_name, len(removed)))

        dispatcher = Dispatcher(tracker, renderer, transformers)

        if renderer is None:
            # dispatcher.parseArguments(**kwargs)
            # result = dispatcher.collect()
            # result = dispatcher.transform()
            result = dispatcher(**kwargs)
            options.do_print = options.language == "notebook"
            options.do_show = False
            options.hardcopy = False
        else:
            # needs to be resolved between renderer and dispatcher options
            result = dispatcher(**kwargs)

        if options.do_print:

            sys.stdout.write(".. ---- TEMPLATE START --------\n\n")

            if options.language == "rst":
                writeRST(sys.stdout,
                         options,
                         kwargs,
                         renderer_options,
                         transformer_options,
                         display_options,
                         tracker_modulename,
                         tracker_name)
            elif options.language == "notebook":
                writeNotebook(sys.stdout,
                              options,
                              kwargs,
                              renderer_options,
                              transformer_options,
                              display_options,
                              tracker_modulename,
                              tracker_name)

            sys.stdout.write("\n.. ---- TEMPLATE END ----------\n")

        sys.stdout.write("\n.. ---- OUTPUT-----------------\n")

        if result and renderer is not None:
            if options.layout is not None:
                lines = Utils.layoutBlocks(result, layout=options.layout)
                print "\n".join(lines)
            else:
                for r in result:
                    if r.title:
                        print ("")
                        print ("title: %s" % r.title)
                        print ("")
                    for s in r:
                        print(str(s))

        if options.hardcopy:

            fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()
            # create all the images
            for figman in fig_managers:
                # create all images
                figid = figman.num
                outfile = re.sub("%s", str(figid), options.hardcopy)
                figman.canvas.figure.savefig(outfile, dpi=options.dpi)

        if result and options.do_show:
            if options.renderer.startswith("r-"):
                for rr in result:
                    for r in rr:
                        if hasattr(r, 'rggplot'):
                            from rpy2.robjects import r as R
                            import rpy2.rinterface
                            try:
                                R.plot(r.rggplot)
                            except rpy2.rinterface.RRuntimeError, msg:
                                if re.search("object.*not found", str(msg)):
                                    print '%s: available columns in dataframe=%s' % \
                                        (msg,
                                          R('''colnames(rframe)'''))

                print("press Ctrl-c to stop")
                while 1:
                    pass

            elif len(_pylab_helpers.Gcf.get_all_fig_managers()) > 0:
                plt.show()

            else:
                for rr in result:
                    for r in rr:
                        if hasattr(r, 'xls'):
                            tmpfile, outpath = tempfile.mkstemp(
                                dir='.', suffix='.xlsx')
                            os.close(tmpfile)
                            print ('saving xlsx to %s' % outpath)
                            r.xls.save(outpath)
                        elif hasattr(r, 'bokeh'):
                            import bokeh.plotting as bk
                            bk.show()

    ######################################################
    # build page
    elif options.page:

        from CGATReport import build
        CGATReport.report_directive.DEBUG = True
        CGATReport.report_directive.FORCE = True

        if not os.path.exists(options.page):
            raise IOError("page %s does not exist" % options.page)

        options.num_jobs = 1

        build.buildPlots(
            [options.page, ], options, [], os.path.dirname(options.page))

        if options.do_show:
            if options.renderer.startswith("r-"):
                print("press Ctrl-c to stop")
                while 1:
                    pass

            elif _pylab_helpers.Gcf.get_all_fig_managers() > 0:
                plt.show()

    else:
        raise ValueError(
            "please specify either a tracker "
            "(-t/--tracker) or a page (-p/--page) to test")

    if savedir is not None:
        os.chdir(savedir)

    if options.tracker and renderer is None:
        datatree = dispatcher.getDataTree()
        dataframe = dispatcher.getDataFrame()

        # trying to push R objects
        # from rpy2.robjects import r as R
        # for k, v in flat_iterator(datatree):
        #     try:
        #         R.assign(k, v)
        #     except ValueError, msg:
        #         print ("could not push %s: %s" % (k,msg))
        #         pass
        # print ("----------------------------------------")
        if options.start_interpreter:
            print ("--> cgatreport - available data structures <--")
            print ("    datatree=%s" % type(datatree))
            print ("    dataframe=%s" % type(dataframe))
            interpreter = code.InteractiveConsole(
                dict(globals().items() + locals().items()))
            interpreter.interact()
            return dataframe
        elif options.start_ipython:
            import IPython
            IPython.embed()
            return dataframe

        return dataframe

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
