import imp
import io
import os
import re
import six
import sys
import types

from logging import debug, warning, critical
from CGATReport.Utils import memoized
from CGATReport.Types import get_encoding

import CGATReport.Plugins
import CGATReport.Plugins.BokehPlotter
import CGATReport.Plugins.BokehPlugin
import CGATReport.Plugins.GGPlotter
import CGATReport.Plugins.HTMLPlugin
import CGATReport.Plugins.MatplotlibPlugin
import CGATReport.Plugins.PandasPlotter
import CGATReport.Plugins.Plotter
import CGATReport.Plugins.RPlotPlugin
import CGATReport.Plugins.RPlotter
import CGATReport.Plugins.RSTPlugin
import CGATReport.Plugins.Renderer
import CGATReport.Plugins.HoloviewsPlotter
import CGATReport.Plugins.HoloviewsPlugin
import CGATReport.Plugins.Seaborn
import CGATReport.Plugins.SlideShow
import CGATReport.Plugins.Transformer
import CGATReport.Plugins.TransformersGeneLists
import CGATReport.Plugins.XLSPlugin
import CGATReport.Plugins.SVGPlugin

CapabilityMap = {
    "collect":
    {
        "matplotlib":
        CGATReport.Plugins.MatplotlibPlugin.MatplotlibPlugin,
        "rplot":
        CGATReport.Plugins.RPlotPlugin.RPlotPlugin,
        "html":
        CGATReport.Plugins.HTMLPlugin.HTMLPlugin,
        "rst":
        CGATReport.Plugins.RSTPlugin.RSTPlugin,
        "xls":
        CGATReport.Plugins.XLSPlugin.XLSPlugin,
        "bokeh":
        CGATReport.Plugins.BokehPlugin.BokehPlugin,
        "svg":
        CGATReport.Plugins.SVGPlugin.SVGPlugin,
        "hv":
        CGATReport.Plugins.HoloviewsPlugin.HoloviewsPlugin,

    },
    "transform":
    {
        "stats":
        CGATReport.Plugins.Transformer.TransformerStats,
        "correlation":
        CGATReport.Plugins.Transformer.TransformerCorrelationPearson,
        "pearson":
        CGATReport.Plugins.Transformer.TransformerCorrelationPearson,
        "contingency":
        CGATReport.Plugins.Transformer.TransformerContingency,
        "spearman":
        CGATReport.Plugins.Transformer.TransformerCorrelationSpearman,
        "test-mwu":
        CGATReport.Plugins.Transformer.TransformerMannWhitneyU,
        "aggregate":
        CGATReport.Plugins.Transformer.TransformerAggregate,
        "histogram":
        CGATReport.Plugins.Transformer.TransformerHistogram,
        "histogram-stats":
        CGATReport.Plugins.Transformer.TransformerHistogramStats,
        "filter":
        CGATReport.Plugins.Transformer.TransformerFilter,
        "pandas":
        CGATReport.Plugins.Transformer.TransformerPandas,
        "melt":
        CGATReport.Plugins.Transformer.TransformerMelt,
        "pivot":
        CGATReport.Plugins.Transformer.TransformerPivot,
        "hypergeometric":
        CGATReport.Plugins.TransformersGeneLists.TransformerHypergeometric,
        "venn":
        CGATReport.Plugins.TransformersGeneLists.TransformerVenn,
        "p-adjust":
        CGATReport.Plugins.TransformersGeneLists.TransformerMultiTest,
        "odds-ratio":
        CGATReport.Plugins.TransformersGeneLists.TransformerOddsRatio,
        },
    "render":
    {
        "user":
        CGATReport.Plugins.Renderer.User,
        "debug":
        CGATReport.Plugins.Renderer.Debug,
        "dataframe":
        CGATReport.Plugins.Renderer.DataFrame,
        "table":
        CGATReport.Plugins.Renderer.Table,
        "rst-table":
        CGATReport.Plugins.Renderer.RstTable,
        "xls-table":
        CGATReport.Plugins.Renderer.XlsTable,
        "html-table":
        CGATReport.Plugins.Renderer.HTMLTable,
        "glossary-table":
        CGATReport.Plugins.Renderer.GlossaryTable,
        "matrix":
        CGATReport.Plugins.Renderer.TableMatrix,
        "matrixNP":
        CGATReport.Plugins.Renderer.NumpyMatrix,
        "status":
        CGATReport.Plugins.Renderer.Status,
        "text":
        CGATReport.Plugins.Plotter.Text,
        "status-matrix":
        CGATReport.Plugins.Renderer.StatusMatrix,
        "line-plot":
        CGATReport.Plugins.Plotter.LinePlot,
        # for backwards compatibility
        "density-plot":
        CGATReport.Plugins.Seaborn.KdePlot,
        "histogram-plot":
        CGATReport.Plugins.Plotter.HistogramPlot,
        "pie-plot":
        CGATReport.Plugins.Plotter.PiePlot,
        "scatter-plot":
        CGATReport.Plugins.Plotter.ScatterPlot,
        "scatter-rainbow-plot":
        CGATReport.Plugins.Plotter.ScatterPlotWithColor,
        "matrix-plot":
        CGATReport.Plugins.Plotter.TableMatrixPlot,
        "matrixNP-plot":
        CGATReport.Plugins.Plotter.NumpyMatrixPlot,
        "hinton-plot":
        CGATReport.Plugins.Plotter.HintonPlot,
        "gallery-plot":
        CGATReport.Plugins.Plotter.GalleryPlot,
        "slideshow-plot":
        CGATReport.Plugins.SlideShow.SlideShowPlot,
        "bar-plot":
        CGATReport.Plugins.Plotter.BarPlot,
        "stacked-bar-plot":
        CGATReport.Plugins.Plotter.StackedBarPlot,
        "interleaved-bar-plot":
        CGATReport.Plugins.Plotter.InterleavedBarPlot,
        "venn-plot":
        CGATReport.Plugins.Plotter.VennPlot,
        # ggplot
        "ggplot":
        CGATReport.Plugins.GGPlotter.GGPlot,
        # holoview
        "hvplot":
        CGATReport.Plugins.HoloviewsPlotter.HoloviewsPlot,
        # pandas plotting
        "pdplot":
        CGATReport.Plugins.PandasPlotter.PandasPlot,
        # seaborn plots
        "sbplot":
        CGATReport.Plugins.Seaborn.SeabornPlot,
        "sb-box-plot":
        CGATReport.Plugins.Seaborn.BoxPlot,
        "sb-violin-plot":
        CGATReport.Plugins.Seaborn.ViolinPlot,
        "sb-kde-plot":
        CGATReport.Plugins.Seaborn.KdePlot,
        "sb-pair-plot":
        CGATReport.Plugins.Seaborn.PairPlot,
        "sb-dist-plot":
        CGATReport.Plugins.Seaborn.DistPlot,
        "sb-heatmap-plot":
        CGATReport.Plugins.Seaborn.HeatmapPlot,
        "sb-clustermap-plot":
        CGATReport.Plugins.Seaborn.ClustermapPlot,
        # R plots
        "r-line-plot":
        CGATReport.Plugins.RPlotter.LinePlot,
        "r-box-plot":
        CGATReport.Plugins.RPlotter.BoxPlot,
        "r-smooth-scatter-plot":
        CGATReport.Plugins.RPlotter.SmoothScatterPlot,
        "r-heatmap-plot":
        CGATReport.Plugins.RPlotter.HeatmapPlot,
        "r-ggplot":
        CGATReport.Plugins.RPlotter.GGPlot,
        # Bokeh plots
        "bk-line-plot":
        CGATReport.Plugins.BokehPlotter.LinePlot,
        "box-plot":
        CGATReport.Plugins.Seaborn.BoxPlot,
        "violin-plot":
        CGATReport.Plugins.Seaborn.ViolinPlot,
    }
}


@memoized
def get_module(name):
    """load module in fullpat
    """
    # remove leading '.'
    debug("entered get_module with `%s`" % name)

    parts = name.split(".")
    if parts[0] == "Tracker":
        # special case: Trackers shipped with CGATReport
        if len(parts) > 2:
            raise NotImplementedError("built-in trackers are Tracker.<name> ")
        name = "Tracker"
        path = [os.path.join(CGATReport.__path__[0])]

    # the first part needs to be on the python sys.path
    elif len(parts) > 1:
        try:
            (file, pathname, description) = imp.find_module(parts[0])
        except ImportError as msg:
            warning("could not find module %s: msg=%s" % (name, msg))
            raise ImportError("could not find module %s: msg=%s" % (name, msg))

        path = [os.path.join(pathname, *parts[1:-1])]
        name = parts[-1]
    else:
        path = None

    debug("searching for module name=%s at path=%s" % (name, str(path)))

    # find module
    try:
        (modulefile, pathname, description) = imp.find_module(name, path)
    except ImportError as msg:
        warning("could not find module %s in %s: msg=%s" % (name, path, msg))
        raise ImportError(
            "could not find module %s in %s: msg=%s" % (name, path, msg))

    if modulefile is None:
        warning("could not find module %s in %s" % (name, path))
        raise ImportError(
            "find_module returned None for %s in %s" %
            (name, path))

    stdout = sys.stdout
    sys.stdout = io.StringIO()
    debug("loading module: %s: %s, %s, %s" %
          (name, modulefile, pathname, description))
    # imp.load_module modifies sys.path - save original and restore
    oldpath = sys.path

    # add to sys.path to ensure that imports in the directory work
    if pathname not in sys.path:
        sys.path.append(os.path.dirname(pathname))

    try:
        module = imp.load_module(name, modulefile, pathname, description)
    except:
        warning("could not load module %s" % name)
        raise
    finally:
        modulefile.close()
        sys.stdout = stdout
        sys.path = oldpath

    return module, pathname


def get_code(cls, pathname):
    '''retrieve code for methods and functions.'''
    # extract code
    code = []
    if six.PY2:
        infile = open(pathname, "r")
    else:
        infile = open(pathname, "r", encoding=get_encoding())

    for line in infile:
        x = re.search("(\s*)(class|def)\s+%s" % cls, line)
        if x:
            indent = len(x.groups()[0])
            code.append(line)
            break
    for line in infile:
        if len(re.match("^(\s*)", line).groups()[0]) <= indent:
            break
        code.append(line)
    infile.close()

    return code


def is_class(obj):
    '''return true if obj is a class.

    return False if it is a function object.
    raise ValueError if neither
    '''

    # checking for subclass of Tracker causes a problem
    # for classes defined in the module Tracker itself.
    # The problem is that 'Tracker' is CGATReport.Tracker.Tracker,
    # while the one in tracker is simply Tracker
    # issubclass(obj, Tracker) and \

    if isinstance(obj, type) and \
            hasattr(obj, "__call__"):
        return True
    elif isinstance(obj, (type, types.FunctionType)):
        return False
    elif isinstance(obj, (type, types.LambdaType)):
        return False

    raise ValueError("can not make sense of tracker %s" % str(obj))


def make_object(path, args=None, kwargs=None):
    '''return object of type *path*

    This function is similar to an import statement, but
    also instantiates the class and returns the object.

    The object is instantiated with *args* and **kwargs**.
    '''

    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    # split class from module
    name, cls = os.path.splitext(path)

    # remove leading '.'
    cls = cls[1:]

    debug("instantiating class %s" % cls)

    module, pathname = get_module(name)

    # get class from module
    try:
        obj = getattr(module, cls)
    except AttributeError:
        raise AttributeError("module %s (%s) has no attribute '%s'" %
                             (module, pathname, cls))
    # instantiate, if it is a class
    if is_class(obj):
        try:
            obj = obj(*args, **kwargs)
        except AttributeError as msg:
            critical("instantiating class %s.%s failed: %s" %
                     (module, cls, msg))
            raise

    return obj, module, pathname, cls


@memoized
def make_tracker(path, args=None, kwargs=None):
    """retrieve an instantiated tracker and its associated code.

    returns a tuple (code, tracker, pathname).
    """
    obj, module, pathname, cls = make_object(path, args, kwargs)
    code = get_code(cls, pathname)
    return code, obj, pathname


@memoized
def make_renderer(path, args=None, kwargs=None):
    """retrieve an instantiated Renderer.

    returns the object.
    """
    obj, module, pathname, cls = make_object(path, args, kwargs)
    return obj


@memoized
def make_transformer(path, args=None, kwargs=None):
    """retrieve an instantiated Transformer.

    returns the object.
    """
    obj, module, pathname, cls = make_object(path, args, kwargs)
    return obj


def get_transformers(transformers, kwargs=None):
    '''find and instantiate all transformers.'''

    if kwargs is None:
        kwargs = {}

    result = []
    for transformer in transformers:
        tt = CapabilityMap["transform"].get(transformer, None)
        if tt is not None:
            instance = tt(**kwargs)
        else:
            instance = make_transformer(transformer, (), kwargs)

        if not instance:
            msg = "could not instantiate transformer '%s'. Available transformers:\n  %s" % \
                (transformer,
                 "\n  ".join(sorted(CapabilityMap["transform"].keys())))
            raise KeyError(msg)

        result.append(instance)

    return result


def get_renderer(renderer_name, kwargs=None):
    '''find and instantiate renderer.'''

    if kwargs is None:
        kwargs = {}

    instance = None

    tt = CapabilityMap["render"].get(renderer_name, None)
    if tt is not None:
        instance = tt(**kwargs)
    else:
        instance = make_renderer(renderer_name, (), kwargs)

    if not instance:
        raise KeyError(
            "could not instantiate renderer '%s'. Available renderers:\n  %s" %
            (renderer_name,
             ",".join(
                 sorted(CapabilityMap["render"].keys()))))

    return instance


def get_plugins(capability):
    return CapabilityMap[capability]


def get_all_plugins():
    return CapabilityMap
