from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReportPlugins.Renderer import Renderer
from CGATReportPlugins.Plotter import parseRanges
from CGATReport import Stats
from CGATReport.DataTree import path2str

from docutils.parsers.rst import directives

import re
try:
    import bokeh.plotting as bk
    HAS_BOKEH = True
except ImportError:
    HAS_BOKEH = False


class BokehPlotter():

    """Base class for Renderers that do simple 2D plotting.

    This mixin class provides convenience function
    for:class:`Renderer.Renderer` classes that do 2D plotting.

    The base class takes care of counting the plots created, provided
    that the methods:meth:`startPlot` and:meth:`endPlot` are called
    appropriately. It then inserts the appropriate place holders.

    This class adds the following options to the:term:`report` directive:

    :term:`logscale`: apply logscales one or more axes.

    :term:`xtitle`: add a label to the X axis

    :term:`ytitle`: add a label to the Y axis

    :term:`title`:  title of the plot

    :term:`add-title`: add title to each plot

    :term:`legend-location`: specify the location of the legend

    :term:`xrange`: restrict plot a part of the x-axis

    :term:`yrange`: restrict plot a part of the y-axis

    :term:`function`: add a function to the plot. Multiple
          functions can be supplied as a ,-separated list.

    :term:`vline`: add one or more vertical lines to the
          plot.

    :term:`xformat`: label for X axis

    :term:`yformat`: label for Y axis

    With some plots default layout options will result in plots
    that are misaligned (legends truncated, etc.). To fix this it might
    be necessary to increase plot size, reduce font size, or others.
    The following options will be passed on the matplotlib to permit
    this control.

    :term:`mpl-figure`: options for matplotlib
           ``figure`` calls().

    :term:`mpl-legend`: options for matplotlib
           ``legend`` calls().

    :term:`mpl-subplot`: options for matplotlib
           ``subplots_adjust`` calls().

    :term:`mpl-rc`: general environment settings for matplotlib.
          See the matplotlib documentation. Multiple options can be
          separated by ;, for example
          ``:mpl-rc: figure.figsize=(20,10);legend.fontsize=4``

    """

    mLegendFontSize = 8
    # number of chars to use to reduce legend font size
    mMaxLegendSize = 100

    # maximum number of rows per column. If there are more,
    # the legend is split into multiple columns
    mLegendMaxRowsPerColumn = 30

    options = (
        ('logscale',  directives.unchanged),
        ('title',  directives.unchanged),
        ('add-title',  directives.flag),
        ('xtitle',  directives.unchanged),
        ('ytitle',  directives.unchanged),
        ('xrange',  directives.unchanged),
        ('yrange',  directives.unchanged),
        ('zrange', directives.unchanged),
        ('function', directives.unchanged),
        ('vline', directives.unchanged),
        ('legend-location',  directives.unchanged),
        ('xformat', directives.unchanged),
        ('yformat', directives.unchanged),
    )

    format_colors = "bgrcmk"
    format_markers = "so^>dph8+x"
    format_lines = ('-', ':', '--')
    mPatterns = [None, '/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']

    def __init__(self, *args, **kwargs):
        """parse option arguments."""

        self.mFigure = 0

        self.logscale = kwargs.get("logscale", None)
        self.title = kwargs.get("title", None)
        self.add_title = "add-title" in kwargs
        self.xlabel = kwargs.get("xtitle", None)
        self.ylabel = kwargs.get("ytitle", None)
        self.functions = kwargs.get("function", None)
        self.vline = kwargs.get("vline", None)
        self.tight_layout = 'tight' in kwargs

        if self.functions:
            if "," in self.functions:
                self.functions = self.functions.split(",")
            else:
                self.functions = [self.functions]

        # substitute '-' in CGATReport-speak for ' ' in matplotlib speak
        self.legend_location = re.sub(
            "-", " ", kwargs.get("legend-location", "upper right"))
        # ("outer-top"))
        self.xrange = parseRanges(kwargs.get("xrange", None))
        self.yrange = parseRanges(kwargs.get("yrange", None))
        self.zrange = parseRanges(kwargs.get("zrange", None))

        self.xformat = kwargs.get("xformat", None)
        self.yformat = kwargs.get("yformat", None)

    def startPlot(self, **kwargs):
        """prepare everything for a plot.

        returns the current figure.
        """
        bk.figure()
        bk.output_file('/dev/null')
        bk.hold()

    def endPlot(self, plts, legends, path):
        """close plots.
        """

        title = path2str(path)
        figid = 10
        lines = []
        plot = self.plots[-1]
        figid = plot._id
        lines.append("")
        lines.append("#$bkh %s$#" % figid)
        lines.append("")
        r = ResultBlock("\n".join(lines), title=title)
        r.bokeh = self.plots[-1]
        return ResultBlocks(r)


class LinePlot(Renderer, BokehPlotter):

    '''create a line plot.

    This:class:`Renderer` requires at least three levels with

    line / label / coords

    This is a base class that provides several hooks for
    derived classes.

    initPlot()

    for line, data in work:
        initLine()

        for label, coords in data:
            xlabel, ylabels = initCoords()
            for ylabel in ylabels:
                addData(xlabel, ylabel)
            finishCoords()
        finishLine()

    finishPlot()

    This plotter accepts the following options:

    :term:`as-lines`: do not plot symbols
    :term:`yerror`: every second data track is a y error

    '''
    nlevels = 2

    options = BokehPlotter.options +\
        (('as-lines', directives.flag),
         ('yerror', directives.flag),
         )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        BokehPlotter.__init__(self, *args, **kwargs)

        self.as_lines = "as-lines" in kwargs

        # data to use for Y error bars
        self.yerror = "yerror" in kwargs

        # do not plot more than ten tracks in one plot
        self.split_at = 10

        self.format_colors = bk.brewer["Spectral"][10]

    def initPlot(self, fig, dataseries, path):
        '''initialize plot.'''

        self.legend = []
        self.plots = []
        self.xlabels = []
        self.ylabels = []

    def getFormat(self, nplotted):
        '''return tuple with color, linestyle and marker for
        data series *n* within a plot.'''

        color = self.format_colors[nplotted % len(self.format_colors)]
        nplotted /= len(self.format_colors)
        linestyle = self.format_lines[nplotted % len(self.format_lines)]
        if self.as_lines:
            marker = None
        else:
            nplotted /= len(self.format_lines)
            marker = self.format_markers[nplotted % len(self.format_markers)]

        return color, linestyle, marker

    def addData(self,
                xvals, yvals,
                xlabel, ylabel,
                nplotted,
                yerrors=None):

        xxvals, yyvals = Stats.filterNone((xvals, yvals))

        color, linestyle, marker = self.getFormat(nplotted)

        self.plots.append(bk.line(
            xxvals,
            yyvals,
            color=color,
            line_width=2))
        # other options:
        # title=...
        # legend=...

    def initLine(self, line, data):
        '''hook for code working on a line.'''
        pass

    def initCoords(self, label, coords):
        '''hook for code working a collection of coords.

        should return a single key for xvalues and
        one or more keys for y-values.
        '''
        keys = list(coords.keys())
        return keys[0], keys[1:]

    def finishCoords(self, label, coords):
        '''hook called after all coords have been processed.'''
        pass

    def finishPlot(self, fig, work, path):
        '''hook called after plotting has finished.'''
        # plt.xlabel("-".join(set(self.xlabels)))
        # plt.ylabel("-".join(set(self.ylabels)))

    def render(self, dataframe, path):

        fig = self.startPlot()

        paths = dataframe.index.get_level_values(0).unique()

        self.initPlot(fig, dataframe, path)

        nplotted = 0

        columns = dataframe.columns

        if len(columns) < 2:
            raise ValueError(
                'require at least two columns, got %i' % len(columns))

        for ppath in paths:
            work = dataframe.ix[ppath]
            xvalues = work[columns[0]]
            for column in work.columns[1:]:

                self.initLine(column, work)

                yvalues = work[column]

                if len(xvalues) != len(yvalues):
                    raise ValueError("length of x,y tuples not consistent: "
                                     "(%s) %i != (%s) %i" %
                                     (columns[0],
                                      len(xvalues),
                                      column,
                                      len(yvalues)))

                self.initCoords(xvalues, yvalues)

                self.addData(xvalues,
                             yvalues,
                             columns[0],
                             column,
                             nplotted)
                nplotted += 1

                # self.legend.append(path2str(ppath) + "/" + column)

        self.finishPlot(fig, dataframe, path)

        return self.endPlot(self.plots, self.legend, path)
