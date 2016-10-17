"""Mixin classes for Renderers that plot.
"""

import os
import re
import math
import itertools
import datetime
import pandas

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReportPlugins.Renderer import Renderer, NumpyMatrix, TableMatrix
from CGATReport.DataTree import path2str, str2path
from CGATReport import DataTree, Stats, Utils

from collections import OrderedDict as odict

from docutils.parsers.rst import directives

import numpy
import matplotlib
matplotlib.use('Agg', warn=False)
# This does not work:
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own
# matplotlibrc.

import matplotlib.colors
import matplotlib.pyplot as plt

# For Rstyle plotting, previously used the snippets from:
# see http://messymind.net/2012/07/making-matplotlib-look-like-ggplot/
# now using seaborn
try:
    import seaborn
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# Python 3 Compatibility
try:
    import matplotlib_venn
except ImportError:
    matplotlib_venn = None


def parseRanges(r):
    '''given a string in the format "x,y",
    return a tuple of values (x,y).

    missing values are set to None.
    '''

    if not r:
        return r
    r = [x.strip() for x in r.split(",")]
    if r[0] == "":
        r[0] = None
    else:
        r[0] = float(r[0])
    if r[1] == "":
        r[1] = None
    else:
        r[1] = float(r[1])
    return r


def normalize_legends(original_legends):

    s = [path2str(x) for x in original_legends]
    paths = [str2path(x) for x in s]

    lengths = [len(x) for x in paths]
    assert min(lengths) == max(lengths)

    levels = list(zip(*paths))
    pruned_levels = [x for x in levels if len(set(x)) > 1]
    
    new_legends = [path2str(x) for x in zip(*pruned_levels)]
    if len(new_legends) != len(original_legends):
        return original_legends
    else:
        return new_legends


class Plotter(object):

    """Base class for Renderers that do simple 2D plotting.

    This mixin class provides convenience function for
    :class:`Renderer.Renderer` classes that do 2D plotting.

    The base class takes care of counting the plots created,
    provided that the methods:meth:`startPlot` and:meth:`endPlot`
    are called appropriately. It then inserts the appropriate place holders.

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
          functions can be supplied as a comma-separated list.
          If functions are separated by a |, then they will
          be plotted on each separately in order, recycling if
          necessary
    
    :term:`vline`: add one or more vertical lines to the
          plot.

    :term:`xformat`: label for X axis

    :term:`yformat`: label for Y axis

    :term:`no-tight`: do not attempt a tight layout
        (see ``matplotlib.pyplot.tight_layout()``)

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

    :term:`xticks-max-chars`: if the number of characters on the
    tick-labels on the X-axis exceed this value, the labels
    will be replaced by shorter version. See :term:`xticks-action`.
    If set to 0, no truncation will be performed.

    :term:`xticks-action`: action to perform it tick-labels are to long.
    Valid values are ``truncate-start`` and ``truncate-end`` to truncate
    from the start or end of the label, respectively; ``numbers`` to
    replace the values with numbers.

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
        ('mpl-figure',  directives.unchanged),
        ('mpl-legend',  directives.unchanged),
        ('mpl-subplot',  directives.unchanged),
        ('mpl-rc',  directives.unchanged),
        ('legend-location',  directives.unchanged),
        ('xformat', directives.unchanged),
        ('yformat', directives.unchanged),
        ('no-tight', directives.flag),  # currently ignored
        ('tight', directives.flag),
        ('xticks-action', directives.unchanged),
        ('xticks-max-chars', directives.length_or_unitless),
    )

    if HAS_SEABORN:
        format_colors = seaborn.color_palette()  # "bgrcmk"
    else:
        format_colors = "bgrcmk"

    format_markers = "so^>dph8+x"
    format_lines = ('-', ':', '--')
    mPatterns = [None, '/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']

    # maximum number of characters in X ticks
    # If 0, do not perform any action
    xticks_max_length = 10

    # action to perform when X ticks are longer than maximum.
    # Options are "truncate-start", "truncate-end", "number"
    xticks_action = "truncate-start"

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
            if "," in self.functions and "|" in self.functions:
                raise ValueError("functions need to be separated by , or |, not both")
                
            self.all_functions_per_plot = True
            if "," in self.functions:
                self.functions = self.functions.split(",")
            elif "|" in self.functions:
                self.all_functions_per_plot = False
                self.functions = self.functions.split("|")
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

        self.xticks_max_length = int(kwargs.get('xticks-max-chars',
                                                self.xticks_max_length))
        self.xticks_action = kwargs.get('xticks-action',
                                        'number')

        if self.xticks_action not in ('number',
                                      'truncate-start',
                                      'truncate-end'):
            raise ValueError(
                "unknown option for xticks-action: '%s'" %
                self.xticks_action)

        def setupMPLOption(key):
            options = {}
            try:
                for k in kwargs[key].split(";"):
                    key, val = k.split("=")
                    # convert unicode to string
                    try:
                        options[str(key)] = eval(val)
                    except NameError:
                        options[str(key)] = val
            except KeyError:
                pass
            return options

        self.mMPLFigureOptions = setupMPLOption("mpl-figure")
        self.mMPLLegendOptions = setupMPLOption("mpl-legend")
        self.mMPLSubplotOptions = setupMPLOption("mpl-subplot")
        self.mMPLRC = setupMPLOption("mpl-rc")

    def startPlot(self, **kwargs):
        """prepare everything for a plot.

        returns the current figure.
        """

        self.mFigure += 1

        # setting rc parameters disabled in order not interfere with seaborn
        # aesthetics
        # go to defaults
        # matplotlib.rcdefaults()

        # set parameters
        # if self.mMPLRC:
        #     self.debug("extra plot options: %s" % str(self.mMPLRC))
        #     matplotlib.rcParams.update(self.mMPLRC)

        self.mCurrentFigure = plt.figure(num=self.mFigure,
                                         **self.mMPLFigureOptions)

        if self.title:
            plt.title(self.title)

        return self.mCurrentFigure

    def wrapText(self, text, cliplen=20, separators=":_"):
        """wrap around text using the mathtext.

        Currently this subroutine uses the \frac directive, so it is
        not pretty.  returns the wrapped text.

        """

        # split txt into two equal parts trying
        # a list of separators
        newtext = []
        for txt in text:
            t = len(txt)
            if t > cliplen:
                for s in separators:
                    parts = txt.split(s)
                    if len(parts) < 2:
                        continue
                    c = 0
                    tt = t // 2
                    # collect first part such that length is
                    # more than half
                    for x, p in enumerate(parts):
                        if c > tt:
                            break
                        c += len(p)

                    # accept if a good split (better than 2/3)
                    if float(c) / t < 0.66:
                        newtext.append(r"$\mathrm{\frac{ %s }{ %s }}$" %
                                       (s.join(parts[:x]), s.join(parts[x:])))
                        break
            else:
                newtext.append(txt)
        return newtext

    def endPlot(self, plts, legends, path):
        """close plots.

        This method performs common post-processing options on
        matplotlib rendered plots:

           * rescaling the axes
           * legend placement and formatting
           * adding a function to the plot

        returns blocks of restructured text with place holders for the
        figure.

        """

        if not plts:
            return ResultBlocks()

        # convert to log-scale
        ax = plt.gca()
        # set logscale before the xlim, as it re-scales the plot.
        if self.logscale:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            if "x" in self.logscale:
                try:
                    ax.set_xscale('log')
                    # rescale: log plots does not autoscale well if
                    # negative values scale manually - needs to be
                    # overridden by the user if small values are to be
                    # expected
                    if xlim[0] < 0:
                        ax.set_xlim((0.01, None))
                except OverflowError:
                    ax.set_xscale('linear')

            if "y" in self.logscale:
                try:
                    ax.set_yscale('log')
                    # rescale: log plots does not autoscale well if
                    # negative values scale manually - needs to be
                    # overridden by the user if small values are to be
                    # expected
                    if ylim[0] < 0:
                        ax.set_ylim((0.01, None))
                except OverflowError:
                    ax.set_yscale('linear')

            ax.relim()

        # truncate plot
        if self.xrange:
            plt.xlim(self.xrange)
        if self.yrange:
            plt.ylim(self.yrange)

        # add additional plot elements
        if self.functions:
            xstart, xend = ax.get_xlim()
            increment = (xend - xstart) / 100.0

            if self.all_functions_per_plot:
                for function in self.functions:
                    f = eval("lambda x: %s" % function)
                    xvals = numpy.arange(xstart, xend, increment)
                    yvals = [f(x) for x in xvals]
                    plt.plot(xvals, yvals)
            else:
                function = self.functions[(self.mFigure - 1) % len(self.functions)]
                f = eval("lambda x: %s" % function)
                xvals = numpy.arange(xstart, xend, increment)
                yvals = [f(x) for x in xvals]
                plt.plot(xvals, yvals)

        if self.vline:
            ystart, yend = ax.get_ylim()
            lines = []
            for l in self.vline.split(","):
                l = l.strip()
                if l == "today":
                    l = datetime.datetime.now().toordinal()
                else:
                    l = int(l)
                lines.append(l)
            ax.vlines(lines, ystart, yend)

        # add labels and titles
        if self.add_title:
            plt.suptitle(DataTree.path2str(path))

        if self.xlabel:
            plt.xlabel(self.xlabel)
        if self.ylabel:
            plt.ylabel(self.ylabel)

        # change x/y labels
        # change x/y axis formatter
        if self.xformat:
            if self.xformat.startswith('date'):
                xlim = ax.get_xlim()
                if xlim[0] < 1:
                    raise ValueError(
                        "date value out of range - needs to larger than 1")

                ax.xaxis_date()
                loc = matplotlib.dates.AutoDateLocator()
                ax.xaxis.set_major_locator(loc)
                fmt = self.xformat[5:].strip()
                if not fmt:
                    fmt = '%Y-%m-%d'
                ax.xaxis.set_major_formatter(
                    matplotlib.dates.AutoDateFormatter(loc,
                                                       defaultfmt=fmt))

        if self.yformat:
            if self.yformat.startswith('date'):
                ylim = ax.get_ylim()
                if ylim[0] < 1:
                    raise ValueError(
                        "date value out of range - needs to larger than 1")

                ax.yaxis_date()
                loc = matplotlib.dates.AutoDateLocator()
                ax.yaxis.set_major_locator(loc)
                fmt = self.yformat[5:].strip()
                if not fmt:
                    fmt = '%Y-%m-%d'
                ax.yaxis.set_major_formatter(
                    matplotlib.dates.AutoDateFormatter(loc,
                                                       defaultfmt=fmt))

        # If longest label on X-axis is larger than
        # threshold, either truncate, summarize or
        # map.
        # modifying labels in place did not work as
        # set_xticklabels expects strings, not Text attributes,
        # so work with text directly:
        preamble, postamble = "", ""
        xlabels = [x.get_text() for x in ax.get_xticklabels()]
        if xlabels and self.xticks_max_length > 0:
            max_len = max([len(x) for x in xlabels])

            if max_len > self.xticks_max_length:

                if self.xticks_action.startswith("truncate"):

                    if self.xticks_action == "truncate-end":
                        f = lambda x, txt: txt[:self.xticks_max_length]
                    elif self.xticks_action == "truncate-start":
                        f = lambda x, txt: txt[-self.xticks_max_length:]
                    new_labels = [f(x, y) for x, y in enumerate(xlabels)]

                elif self.xticks_action == "number":
                    # Use chars starting at 'A' for labels
                    nchars = int(math.ceil(len(xlabels) / 26.0))
                    new_labels = ["".join(x) for x in itertools.product(
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                        repeat=nchars)]
                    new_labels = new_labels[:len(xlabels)]
                else:
                    raise ValueError(
                        "unkown xtick-action: {}".format(self.xticks_action))

                postamble = "\n" + "\n".join(
                    ["* %s: %s" % (x, y)
                     for x, y in zip(new_labels, xlabels)])

                ax.set_xticklabels(new_labels)

        blocks = ResultBlocks(
            ResultBlock(
                text="#$mpl %i$#\n" % self.mFigure,
                title=DataTree.path2str(path),
                preamble=preamble,
                postamble=postamble))

        legend = None
        maxlen = 0

        # In matplotlib version < 1.1, the output of plotting was
        # a single element. In later versions, the output is a tuple
        # so take first element.
        if type(plts[0]) in (tuple, list):
            plts = [x[0] for x in plts]

        # convert to string
        if legends:
            legends = normalize_legends(legends)

        if self.legend_location != "none" and plts and legends:

            maxlen = max([len(x) for x in legends])
            # legends = self.wrapText(legends)

            assert len(plts) == len(legends)
            if self.legend_location.startswith("outer"):
                legend = outer_legend(plts,
                                      legends,
                                      loc=self.legend_location,
                                      ncol=1,
                                      )
            else:
                # do not use plt.figlegend
                # as legend disappears in mpld3
                ax.legend(plts,
                          legends,
                          loc=self.legend_location,
                          ncol=1,
                          **self.mMPLLegendOptions)

        if self.legend_location == "extra" and legends:

            blocks.append(
                ResultBlock("\n".join(("#$mpl %i$#" % self.mFigure, "")),
                            "legend"))
            self.mFigure += 1
            legend = plt.figure(self.mFigure, **self.mMPLFigureOptions)
            lx = legend.add_axes((0.1, 0.1, 0.9, 0.9))
            lx.set_title("Legend")
            lx.set_axis_off()
            plt.setp(lx.get_xticklabels(), visible=False)
            if not plts:
                plts = []
                for x in legends:
                    plts.append(plt.plot((0,), (0,)))

            lx.legend(
                plts, legends,
                'center left',
                ncol=max(
                    1, int(math.ceil(float(len(legends) /
                                           self.mLegendMaxRowsPerColumn)))),
                **self.mMPLLegendOptions)

        # smaller font size for large legends
        if legend and maxlen > self.mMaxLegendSize:
            # all the text.Text instance in the legend
            ltext = legend.get_texts()
            plt.setp(ltext, fontsize='small')

        if self.mMPLSubplotOptions:
            # apply subplot options - useful even if there are no subplots in
            # order to set figure margins.
            plt.subplots_adjust(**self.mMPLSubplotOptions)

        # disabled: tight_layout not working well sometimes
        # causing plots to display compressed
        if self.tight_layout:
            try:
                plt.tight_layout()
            except ValueError:
                # some plots (with large legends) receive
                # ValueError("bottom cannot be >= top")
                pass

        return blocks

    def rescaleForVerticalLabels(self, labels, offset=0.02, cliplen=6):
        """rescale current plot so that vertical labels are displayed
        properly.

        In some plots the labels are clipped if the labels are
        vertical labels on the X-axis.  This is a heuristic hack and
        is not guaranteed to always work.

        """
        # rescale plotting area if labels are more than 6 characters
        if len(labels) == 0:
            return

        maxlen = max([len(str(x)) for x in labels])
        if maxlen > cliplen:
            currentAxes = plt.gca()
            currentAxesPos = currentAxes.get_position()

            # scale plot by 2% for each extra character
            # scale at most 30% as otherwise the plot will
            # become illegible (and matplotlib might crash)
            offset = min(0.3, offset * (maxlen - cliplen))

            # move the x-axis up
            currentAxes.set_position((currentAxesPos.xmin,
                                      currentAxesPos.ymin + offset,
                                      currentAxesPos.width,
                                      currentAxesPos.height - offset))


class PlotterMatrix(Plotter):

    """Plot a matrix.

    This mixin class provides convenience function
    for:class:`Renderer.Renderer` classes that plot matrices.

    This class adds the following options to the:term:`report` directive:

    :term:`colorbar-format`: numerical format for the colorbar.

    :term:`palette`: numerical format for the colorbar.

    :term:`reverse-palette`: invert palette

    :term:`max-rows`: maximum number of rows per plot

    :term:`max-cols`: maximum number of columns per plot

    :term:`nolabel-rows`: do not add row labels

    :term:`nolabel-cols`: do not add column labels

    """

    mFontSize = 8

    # after # characters, split into two
    # lines
    mSplitHeader = 20
    mFontSizeSplit = 8

    # separators to use to split text
    mSeparators = ":_"

    options = Plotter.options +\
        (('palette', directives.unchanged),
         ('reverse-palette', directives.flag),
         ('split-rows', directives.unchanged),
         ('split-cols', directives.unchanged),
         ('colorbar-format', directives.unchanged),
         ('nolabel-rows', directives.flag),
         ('nolabel-cols', directives.flag),
         )

    def __init__(self, *args, **kwargs):
        Plotter.__init__(self, *args, **kwargs)

        self.mBarFormat = kwargs.get("colorbar-format", "%1.1f")
        self.mPalette = kwargs.get("palette", "jet")
        self.split_rows = kwargs.get("split-rows", 0)
        self.split_cols = kwargs.get("split-cols", 0)

        self.mReversePalette = "reverse-palette" in kwargs
        self.label_rows = "nolabel-rows" not in kwargs
        self.label_cols = "nolabel-cols" not in kwargs

    def addColourBar(self, ax=None):
        if ax is None:
            plt.colorbar(format=self.mBarFormat)
        else:
            fig = ax.figure
            fig.subplots_adjust(right=0.8)
            cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
            fig.colorbar(ax, cax=cbar_ax, format=self.mBarFormat)

    def buildWrappedHeaders(self, headers):
        """build headers. Long headers are split using
        the \frac mathtext directive (mathtext does not
        support multiline equations.

        This method is currently not in use.

        returns (fontsize, headers)
        """

        fontsize = self.mFontSize
        maxlen = max([len(x) for x in headers])

        if maxlen > self.mSplitHeader:
            h = []
            fontsize = self.mFontSizeSplit

            for header in headers:
                if len(header) > self.mSplitHeader:
                    # split txt into two equal parts trying
                    # a list of separators
                    t = len(header)
                    for s in self.mSeparators:
                        parts = header.split(s)
                        if len(parts) < 2:
                            continue
                        c = 0
                        tt = t // 2
                        # collect first part such that length is
                        # more than half
                        for x, p in enumerate(parts):
                            if c > tt:
                                break
                            c += len(p)

                        # accept if a good split (better than 2/3)
                        if float(c) / t < 0.66:
                            h.append(r"$\mathrm{\frac{ %s }{ %s }}$" %
                                     (s.join(parts[:x]), s.join(parts[x:])))
                            break
                    else:
                        h.append(header)
                else:
                    h.append(header)
            headers = h

        return fontsize, headers

    def plotMatrix(self, matrix, row_headers, col_headers,
                   vmin, vmax,
                   color_scheme=None):

        self.debug("plot matrix started")
        # when matrix is very different from square matrix
        # adjust figure size
        # better would be to move the axes as well to the left of
        # the figure.
        if len(row_headers) > 2 * len(col_headers):
            r = float(len(row_headers)) / len(col_headers) * 0.5
            w, h = self.mCurrentFigure.get_size_inches()
            self.mCurrentFigure.set_size_inches(w, h * r)
        elif len(col_headers) > 2 * len(row_headers):
            r = float(len(col_headers)) / len(row_headers)
            w, h = self.mCurrentFigure.get_size_inches() * 0.5
            self.mCurrentFigure.set_size_inches(w * r, h)

        if self.logscale is not None and "z" in self.logscale:
            norm = matplotlib.colors.LogNorm(vmin, vmax)
        else:
            norm = None

        plot = plt.imshow(matrix,
                          cmap=color_scheme,
                          origin='lower',
                          vmax=vmax,
                          vmin=vmin,
                          norm=norm,
                          interpolation='nearest')

        # offset=0: x=center,y=center
        # offset=0.5: y=top/x=right
        offset = 0.0

        if self.label_rows:
            row_headers = [str(x) for x in row_headers]
            yfontsize, row_headers = self.mFontSize, row_headers
            plt.yticks([offset + y for y in range(len(row_headers))],
                       row_headers,
                       fontsize=yfontsize)

        if self.label_cols:
            col_headers = [str(x) for x in col_headers]
            xfontsize, col_headers = self.mFontSize, col_headers
            plt.xticks([offset + x for x in range(len(col_headers))],
                       col_headers,
                       rotation="vertical",
                       fontsize=xfontsize)

        # turn off any grid lines
        plt.grid(False)
        self.debug("plot matrix finished")

        return plot

    def plot(self, matrix, row_headers, col_headers, path):
        '''plot matrix.

        Large matrices are split into several plots.
        '''

        self.debug("plot started")

        self.startPlot()

        nrows, ncols = matrix.shape
        if self.zrange:
            vmin, vmax = self.zrange
            if vmin is None:
                vmin = matrix.min()
            if vmax is None:
                vmax = matrix.max()
            matrix[matrix < vmin] = vmin
            matrix[matrix > vmax] = vmax
        else:
            vmin, vmax = None, None

        if self.mPalette:
            try:
                if self.mReversePalette:
                    color_scheme = eval("plt.cm.%s_r" % self.mPalette)
                else:
                    color_scheme = eval("plt.cm.%s" % self.mPalette)
            except AttributeError:
                raise ValueError("unknown palette '%s'" % self.mPalette)
        else:
            color_scheme = None

        plots, labels = [], []

        if self.split_cols == "auto":
            self.split_cols = int(ncols / math.sqrt(ncols / nrows))
        else:
            self.split_cols = int(self.split_cols)

        if self.split_rows == "auto":
            self.split_rows = int(nrows / math.sqrt(nrows / ncols))
        else:
            self.split_rows = int(self.split_rows)
            
        split_row = self.split_rows > 0 and nrows > self.split_rows
        split_col = (self.split_cols > 0 and ncols > self.split_cols) or \
                    (self.split_cols == "auto")

        # set consistent min/max values
        if split_row or split_col:
            if vmin is None:
                vmin = numpy.nanmin(matrix)
                if vmin == numpy.inf or vmin == -numpy.inf:
                    vmin = numpy.nanmin(matrix[matrix != vmin])
            if vmax is None:
                vmax = numpy.nanmax(matrix)
                if vmax == numpy.inf or vmax == -numpy.inf:
                    vmax = numpy.nanmax(matrix[matrix != vmax])

        if (split_row and split_col) or not (split_row or split_col):
            self.debug("not splitting matrix")
            # do not split small or symmetric matrices

            cax = self.plotMatrix(matrix, row_headers, col_headers,
                                  vmin, vmax, color_scheme)
            plots.append(cax)
            # plots, labels = None, None
            self.rescaleForVerticalLabels(col_headers, cliplen=12)
            self.addColourBar()

        elif split_row:
            nplots = int(math.ceil(float(nrows) / self.split_rows))

            self.debug("splitting matrix at rows: {} * {} x {}".format(
                nplots, self.split_rows, ncols))
            
            # not sure why this switch to numbers - disable
            # new_headers = ["%s" % (x + 1) for x in range(len(row_headers))]
            new_headers = row_headers
            for x in range(nplots):
                plt.subplot(1, nplots, x + 1)
                start = x * self.split_rows
                end = start + min(nrows, self.split_rows)
                cax = self.plotMatrix(matrix[start:end, :],
                                      new_headers[start:end],
                                      col_headers,
                                      vmin, vmax,
                                      color_scheme)
                plots.append(cax)
            # labels = ["%s: %s" % x for x in zip(new_headers, row_headers) ]

            self.legend_location = "extra"
            plt.subplots_adjust(**self.mMPLSubplotOptions)
            self.addColourBar()

        elif split_col:
            nplots = int(math.ceil(float(ncols) / self.split_cols))
            self.debug("splitting matrix at columns: {} * {} x {}".format(
                nplots, nrows, self.split_cols))

            # not sure why this switch to numbers - disable
            # new_headers = ["%s" % (x + 1) for x in range(len(col_headers))]
            new_headers = col_headers
            for x in range(nplots):
                plt.subplot(nplots, 1, x + 1)
                start = x * self.split_cols
                end = start + min(ncols, self.split_cols)
                cax = self.plotMatrix(matrix[:, start:end],
                                      row_headers,
                                      new_headers[start:end],
                                      vmin, vmax,
                                      color_scheme)
                plots.append(cax)
            # labels = ["%s: %s" % x for x in zip(new_headers, col_headers) ]

            self.legend_location = "extra"
            plt.subplots_adjust(**self.mMPLSubplotOptions)
            self.addColourBar(ax=cax)

        self.debug("plot finished")

        return self.endPlot(plots, labels, path)


class PlotterHinton(PlotterMatrix):

    '''plot a hinton diagram.

    Draws a Hinton diagram for visualizing a weight matrix.

    The size of a box reflects the weight.

    Taken from http://www.scipy.org/Cookbook/Matplotlib/HintonDiagrams
    and modified to add colours, labels, etc.
    '''

    # column to use for error bars
    colour_matrix = None

    def __init__(self, *args, **kwargs):
        PlotterMatrix.__init__(self, *args, **kwargs)

    def addColourBar(self):

        axc, kw = matplotlib.colorbar.make_axes(plt.gca())
        cb = matplotlib.colorbar.ColorbarBase(axc,
                                              cmap=self.color_scheme,
                                              norm=self.normer)

        cb.draw_all()

    def buildMatrices(self, work, **kwargs):
        '''build matrices necessary for plotting.
        '''
        self.colour_matrix = None

        if self.colour:
            # select label to take
            labels = DataTree.getPaths(work)
            label = list(set(labels[-1]).difference(set((self.colour,))))[0]
            self.matrix, self.rows, self.columns = TableMatrix.buildMatrix(
                self,
                work,
                apply_transformations=True,
                take=label,
                **kwargs
            )

            if self.colour and self.colour in labels[-1]:
                self.colour_matrix, rows, colums = TableMatrix.buildMatrix(
                    self,
                    work,
                    apply_transformations=False,
                    take=self.colour,
                    **kwargs
                )

        else:
            self.matrix, self.rows, self.columns = TableMatrix.buildMatrix(
                self, work, **kwargs)

        return self.matrix, self.rows, self.columns

    def plotMatrix(self, weight_matrix,
                   row_headers, col_headers,
                   vmin, vmax,
                   color_scheme=None):
        """
        Temporarily disables matplotlib interactive mode if it is on,
        otherwise this takes forever.
        """
        def _blob(x, y, area, colour):
            """
            Draws a square-shaped blob with the given area (< 1) at
            the given coordinates.
            """
            hs = numpy.sqrt(area) / 2
            xcorners = numpy.array([x - hs, x + hs, x + hs, x - hs])
            ycorners = numpy.array([y - hs, y - hs, y + hs, y + hs])
            plt.fill(xcorners, ycorners,
                     edgecolor=colour,
                     facecolor=colour)

        plt.clf()

        # convert to real-valued data
        weight_matrix = numpy.nan_to_num(weight_matrix)

        height, width = weight_matrix.shape
        if vmax is None:
            # 2**numpy.ceil(numpy.log(numpy.max(numpy.abs(weight_matrix)))/numpy.log(2))
            vmax = weight_matrix.max()
        if vmin is None:
            vmin = weight_matrix.min()

        scale = vmax - vmin

        if self.colour_matrix is not None:
            colour_matrix = self.colour_matrix
        else:
            colour_matrix = weight_matrix

        cmin, cmax = colour_matrix.min(), colour_matrix.max()

        plot = None
        normer = matplotlib.colors.Normalize(cmin, cmax)
        # save for colourbar
        self.normer = normer
        self.color_scheme = color_scheme

        colours = normer(colour_matrix)

        plt.axis('equal')

        for x in range(width):
            for y in range(height):
                _x = x + 1
                _y = y + 1
                weight = weight_matrix[y, x] - vmin

                _blob(_x - 0.5,
                      _y - 0.5,
                      weight / scale,
                      color_scheme(colours[y, x]))

        offset = 0.5
        xfontsize, col_headers = self.mFontSize, col_headers
        yfontsize, row_headers = self.mFontSize, row_headers

        plt.xticks([offset + x for x in range(len(col_headers))],
                   col_headers,
                   rotation="vertical",
                   fontsize=xfontsize)

        plt.yticks([offset + y for y in range(len(row_headers))],
                   row_headers,
                   fontsize=yfontsize)

        return plot


def on_draw(event):
    '''resize for figure legend.'''

    # locate figure and axes
    canvas = event.canvas
    fig = canvas.figure
    axes = fig.gca()

    # get figure coordinates
    dpi = fig.get_dpi()
    width, height = fig.get_size_inches()
    max_x, max_y = dpi * width, dpi * height

    # find legend and coords
    for o in fig.findobj(matplotlib.legend.Legend):
        legend = o

    legend_coords = legend.get_window_extent().get_points()
    legend_x, legend_y = legend_coords[1]

    # re-scale
    if legend_x > max_x:
        scale_x = legend_x / max_x * 1.1
    else:
        scale_x = 1.0

    if legend_y > max_y:
        scale_y = legend_y / max_y * 1.1
    else:
        scale_y = 1.0

    pos = axes.get_position()
    # re-scale axes to create space for legend
    axes.set_position((pos.xmin,
                       pos.ymin,
                       pos.width * 1.0 / scale_x,
                       pos.height * 1.0 / scale_y))

    # scale figure
    fig.set_figwidth(fig.get_figwidth() * scale_x)
    fig.set_figheight(fig.get_figheight() * scale_y)

    # redraw, temporarily disable event to avoid infinite recursion
    func_handles = fig.canvas.callbacks.callbacks[event.name]
    canvas.callbacks.callbacks[event.name] = {}
    # redraw the figure..
    canvas.draw()
    # reset the draw event callbacks
    fig.canvas.callbacks.callbacks[event.name] = func_handles

    return False


def outer_legend(*args, **kwargs):
    """plot legend outside of plot by rescaling it.

    Copied originally from
    http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg04256.html
    but modified.

    There were problems with the automatic re-scaling of the
    plot. Basically, the legend size seemed to be unknown and set to
    0,0,1,1. Only after plotting were the correct bbox coordinates
    entered.

    The current implementation allocates 3/4 of the canvas for the
    legend and hopes for the best.

    """

    # make a legend without the location
    # remove the location setting from the kwargs
    if 'loc' in kwargs:
        loc = kwargs.pop('loc')
    else:
        loc == "outer-top"

    if loc.endswith("right"):
        leg = plt.legend(bbox_to_anchor=(1.05, 1), loc=2,
                         borderaxespad=0., mode="expand", *args, **kwargs)
    elif loc.endswith("top"):
        leg = plt.legend(
            bbox_to_anchor=(0, 1.02, 1., 1.02), loc=3,
            mode="expand", *args, **kwargs)
    else:
        raise ValueError("unknown legend location %s" % loc)

    fig = plt.gcf()
    cid = fig.canvas.mpl_connect('draw_event', on_draw)
    return leg

# the following has been taken from
# http://www.scipy.org/Cookbook/Matplotlib/HintonDiagrams


def hinton(W, maxWeight=None):
    """
    Draws a Hinton diagram for visualizing a weight matrix.
    Temporarily disables matplotlib interactive mode if it is on,
    otherwise this takes forever.
    """
    def _blob(x, y, area, colour):
        """
        Draws a square-shaped blob with the given area (< 1) at
        the given coordinates.
        """
        hs = numpy.sqrt(area) / 2
        xcorners = numpy.array([x - hs, x + hs, x + hs, x - hs])
        ycorners = numpy.array([y - hs, y - hs, y + hs, y + hs])
        plt.fill(xcorners, ycorners, colour, edgecolor=colour)

    reenable = False
    if plt.isinteractive():
        reenable = True
        plt.ioff()

    plt.clf()

    height, width = W.shape
    if not maxWeight:
        maxWeight = 2 ** numpy.ceil(
            numpy.log(numpy.max(numpy.abs(W))) / numpy.log(2))

    plot = plt.fill(
        numpy.array([0, width, width, 0]),
        numpy.array([0, 0, height, height]), 'gray')

    plt.axis('off')
    plt.axis('equal')
    for x in range(width):
        for y in range(height):
            _x = x + 1
            _y = y + 1
            w = W[y, x]
            if w > 0:
                _blob(
                    _x - 0.5, height - _y + 0.5,
                    min(1, w / maxWeight), 'white')
            elif w < 0:
                _blob(
                    _x - 0.5, height - _y + 0.5,
                    min(1, -w / maxWeight), 'black')

    if reenable:
        plt.ion()

    return plot


class LinePlot(Renderer, Plotter):

    '''create a line plot.

    Plot lines from a dataframe. Separate lines are defined
    by:

    1. multiple columns in the dataframe
    2. mulitple indices in the dataframe

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
    nlevels = 1

    options = Plotter.options +\
        (('as-lines', directives.flag),
         ('yerror', directives.flag),
         )

    # when splitting, keep first column (X coordinates)
    split_keep_first_column = True

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        self.as_lines = "as-lines" in kwargs

        # data to use for Y error bars
        self.yerror = "yerror" in kwargs

        # do not plot more than ten tracks in one plot
        if self.split_at == 0:
            self.split_at = 10

        self.split_at = min(self.split_at, 10)

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
        nplotted //= len(self.format_colors)
        linestyle = self.format_lines[nplotted % len(self.format_lines)]
        if self.as_lines:
            marker = None
        else:
            nplotted //= len(self.format_lines)
            marker = self.format_markers[nplotted % len(self.format_markers)]

        return color, linestyle, marker

    def addData(self,
                xvals,
                yvals,
                xlabel,
                ylabel,
                nplotted,
                yerrors=None):

        xxvals, yyvals = Stats.filterNone((xvals, yvals))

        color, linestyle, marker = self.getFormat(nplotted)

        if yerrors:
            self.plots.append(plt.errorbar(xxvals,
                                           yyvals,
                                           yerr=yerrors,
                                           label=ylabel,
                                           color=color,
                                           linestyle=linestyle,
                                           marker=marker))

        else:
            self.plots.append(plt.plot(xxvals,
                                       yyvals,
                                       color=color,
                                       linestyle=linestyle,
                                       marker=marker,
                                       label=ylabel))

        self.ylabels.append(path2str(ylabel))
        self.xlabels.append(path2str(xlabel))

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
        plt.xlabel("-".join(set(self.xlabels)))
        plt.ylabel("-".join(set(self.ylabels)))

    def render(self, dataframe, path):

        fig = self.startPlot()

        self.initPlot(fig, dataframe, path)

        nplotted = 0

        columns = dataframe.columns

        if len(columns) < 2:
            raise ValueError(
                'require at least two columns, got %i' % len(columns))

        level = Utils.getGroupLevels(dataframe)
        for key, work in dataframe.groupby(
                level=level):
            xvalues = work[columns[0]]
            for column in work.columns[1:]:
                self.initLine(column, work)

                yvalues = work[column]

                if len(xvalues) != len(yvalues):
                    raise ValueError(
                        "length of x,y tuples not consistent: "
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

                self.legend.append(path2str(key) + "/" + column)

        self.finishPlot(fig, dataframe, path)

        return self.endPlot(self.plots, self.legend, path)


class HistogramPlot(LinePlot):

    '''create a line plot.

    This:class:`Renderer` requires at least three levels:

    Currently the xvalues are interpreted as left bin sizes
    and the last bin is the same width as the second to last
    bin. This could be made more correct using the bins
    from histogram directly.

    line / data / coords.
    '''
    nlevels = 2

    # column to use for error bars
    error = None

    options = LinePlot.options +\
        (('error', directives.unchanged),)

    def __init__(self, *args, **kwargs):
        LinePlot.__init__(self, *args, **kwargs)

        try:
            self.error = kwargs["error"]
        except KeyError:
            pass

    def initCoords(self, xvalues, yvalues):
        '''collect error coords and compute bar width.'''

        self.yerr = None
        # locate error bars
        # if self.error and self.error in coords:
        #     self.yerr = coords[self.error]
        #     ylabels = [ x for x in ylabels if x == self.error ]
        # else:
        #     self.yerr = None

        # compute bar widths
        widths = []
        xv = numpy.array(xvalues)
        w = xv[0]
        for x in xv[1:]:
            widths.append(x - w)
            w = x
        widths.append(widths[-1])

        self.widths = widths

    def addData(self,
                xvals,
                yvals,
                xlabel,
                ylabel,
                nplotted,
                yerrors=None):

        alpha = 1.0 / (nplotted + 1)
        self.plots.append(plt.bar(
            list(xvals),
            list(yvals),
            width=self.widths,
            alpha=alpha,
            yerr=self.yerr,
            color=self.format_colors[nplotted % len(self.format_colors)],))

        self.ylabels.append(path2str(ylabel))
        self.xlabels.append(path2str(xlabel))

    def finishPlot(self, fig, work, path):

        LinePlot.finishPlot(self, fig, work, path)
        # there is a problem with legends
        # even though len(plts) == len(legend)
        # matplotlib thinks there are more.
        # In fact, it thinks it is len(plts) = len(legend) * len(xvals)
        self.legend = None


class HistogramGradientPlot(LinePlot):

    '''create a series of coloured bars from histogram data.

    This:class:`Renderer` requires at least three levels:

    line / data / coords.
    '''
    nlevels = 2

    options = LinePlot.options +\
        (('palette', directives.unchanged),
         ('reverse-palette', directives.flag),
         ('colorbar-format', directives.unchanged))

    def __init__(self, *args, **kwargs):
        LinePlot.__init__(self, *args, **kwargs)

        try:
            self.mBarFormat = kwargs["colorbar-format"]
        except KeyError:
            self.mBarFormat = "%1.1f"

        try:
            self.mPalette = kwargs["palette"]
        except KeyError:
            self.mPalette = "Blues"

        self.mReversePalette = "reverse-palette" in kwargs

        if self.mPalette:
            if self.mReversePalette:
                self.color_scheme = plt.get_cmap("%s_r" % self.mPalette)
            else:
                self.color_scheme = plt.get_cmap("%s" % self.mPalette)
        else:
            self.color_scheme = None

        raise NotImplementedError(
            'histogram-gradient-plot needs to be updated')

    def initPlot(self, fig, dataseries, path):

        LinePlot.initPlot(self, fig, dataseries, path)

        # get min/max x and number of rows
        xmin, xmax = None, None
        ymin, ymax = None, None
        nrows = 0
        self.xvals = None

        work = dataseries.unstack()

        for line, data in list(work.items()):

            for label, coords in list(data.items()):

                try:
                    keys = list(coords.keys())
                except AttributeError:
                    continue
                if len(keys) <= 1:
                    continue

                xvals = coords[keys[0]]
                if self.xvals is None:
                    self.xvals = xvals
                elif not numpy.all(self.xvals == xvals):
                    raise ValueError(
                        "Gradient-Histogram-Plot requires the same x values.")

                if xmin is None:
                    xmin, xmax = min(xvals), max(xvals)
                else:
                    xmin = min(xmin, min(xvals))
                    xmax = max(xmax, max(xvals))

                for ylabel in keys[1:]:
                    yvals = coords[ylabel]
                    if ymin is None:
                        ymin, ymax = min(yvals), max(yvals)
                    else:
                        ymin = min(ymin, min(yvals))
                        ymax = max(ymax, max(yvals))

                nrows += len(keys) - 1

        self.nrows = nrows
        self.ymin, self.ymax = ymin, ymax

        if self.zrange:
            self.ymin, self.ymax = self.zrange

    def addData(self, line, label, xlabel, ylabel,
                xvals, yvals, nplotted,
                yerrors=None):

        if self.zrange:
            vmin, vmax = self.zrange
            if vmin is None:
                vmin = yvals.min()
            if vmax is None:
                vmax = yvals.max()
            yvals[yvals < vmin] = vmin
            yvals[yvals > vmax] = vmax

        a = numpy.vstack((yvals, yvals))

        ax = plt.subplot(self.nrows, 1, nplotted + 1)
        self.plots.append(plt.imshow(a,
                                     aspect='auto',
                                     cmap=self.color_scheme,
                                     origin='lower',
                                     vmax=self.ymax,
                                     vmin=self.ymin))

        # add legend on left-hand side
        pos = list(ax.get_position().bounds)
        self.mCurrentFigure.text(pos[0] - 0.01,
                                 pos[1],
                                 line,
                                 horizontalalignment='right')

        ax = plt.gca()
        plt.setp(ax.get_xticklabels(), visible=False)
        plt.setp(ax.get_yticklabels(), visible=False)

    def finishPlot(self, fig, work, path):

        ax = plt.gca()
        plt.setp(ax.get_xticklabels(), visible=True)
        increment = len(self.xvals) // 5
        ax.set_xticks(list(range(0, len(self.xvals), increment)))
        ax.set_xticklabels([self.xvals[x]
                            for x in range(0, len(self.xvals), increment)])

        LinePlot.finishPlot(self, fig, work, path)
        self.legend = None

        # add colorbar on the right
        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
        cax = plt.axes([0.85, 0.1, 0.075, 0.8])
        plt.colorbar(cax=cax, format=self.mBarFormat)


class BarPlot(TableMatrix, Plotter):

    '''A bar plot.

    This:class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    '''

    options = TableMatrix.options + Plotter.options +\
        (('label', directives.unchanged),
         ('error', directives.unchanged),
         ('colour', directives.unchanged),
         ('transparency', directives.unchanged),
         ('bottom-value', directives.unchanged),
         ('orientation', directives.unchanged),
         ('first-is-offset', directives.unchanged),
         ('switch', directives.unchanged),
         ('bar-width', directives.unchanged),
         )

    # column to use for error bars
    error = None

    # column to use for labels
    label = None

    # column to use for custom colours
    colour = None

    # column to use for transparency values
    # transparency does not work yet - bar plot does not
    # accept a list of transparency values
    transparency = None

    # bottom value of bars (can be used to move intersection of x-axis with
    # y-axis)
    bottom_value = None

    label_offset_x = 10
    label_offset_y = 5

    # orientation of bars
    orientation = 'vertical'

    # first row is offset (not plotted)
    first_is_offset = False

    # switch rows/columns
    switch_row_col = False

    # bar width (height for horizontal plots)
    bar_width = 0.5

    # always put multiple bars in a plot
    group_level = -1

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        self.error = kwargs.get("error", None)
        self.label = kwargs.get("label", None)
        self.colour = kwargs.get("colour", None)
        self.switch_row_col = 'switch' in kwargs
        self.transparency = kwargs.get("transparency", None)
        if self.transparency:
            raise NotImplementedError("transparency not implemented yet")
        self.orientation = kwargs.get('orientation', 'vertical')

        if 'bar-width' in kwargs:
            self.bar_width = float(kwargs.get('bar-width'))

        self.barlog = False
        if self.orientation == 'vertical':
            # bar functions require log parameter
            if self.logscale and "y" in self.logscale:
                self.barlog = True
            # erase other log transformations
            self.logscale = None
            self.plotf = plt.bar

        else:
            if self.logscale and "x" in self.logscale:
                self.barlog = True
            self.logscale = None
            self.plotf = plt.barh

        self.bottom_value = kwargs.get("bottom-value", None)
        self.first_is_offset = 'first-is-offset' in kwargs

        self.bar_patterns = list(itertools.product(self.mPatterns,
                                                   self.format_colors))

    def addLabels(self, xvals, yvals, labels):
        '''add labels at x,y at current plot.
        '''

        def coord_offset(ax, fig, x, y):
            return matplotlib.transforms.offset_copy(
                ax.transData,
                fig, x=x, y=y, units='dots')

        if self.orientation == 'horizontal':
            xvals, yvals = yvals, xvals

        ax = plt.gca()
        trans = coord_offset(ax, self.mCurrentFigure,
                             self.label_offset_x,
                             self.label_offset_y)

        for xval, yval, label in zip(xvals, yvals, labels):
            ax.text(xval, yval, label, transform=trans)

    def buildMatrices(self, dataframe):
        '''build matrices necessary for plotting.

        If a matrix only contains a single row, the matrix
        is transposed.
        '''

        def _getMatrix(l, dataframe):
            if l is None:
                return None
            m = dataframe[l]
            try:
                m = m.unstack()
                return m.as_matrix()
            except AttributeError:
                # is not a multi-index object, no need to unstack
                m = m.as_matrix()
                m.shape = len(m), 1
                return m

        self.error_matrix = _getMatrix(self.error, dataframe)
        self.label_matrix = _getMatrix(self.label, dataframe)
        self.colour_matrix = _getMatrix(self.colour, dataframe)
        self.transparency_matrix = _getMatrix(self.transparency, dataframe)

        # remove the special columns
        if self.error or self.label or self.colour or self.transparency:
            dataframe = dataframe[
                [x for x in dataframe.columns
                 if x not in (self.error, self.label,
                              self.colour, self.transparency)]]

        # take first of the remaining columns ignoring the rest
        try:
            df = dataframe[dataframe.columns[0]].unstack()
        except AttributeError:
            # is not a multi-index object, no need to unstack
            df = dataframe

        self.rows = [path2str(x) for x in list(df.index)]
        self.columns = list(df.columns)
        self.data_matrix = df.as_matrix()

        if self.switch_row_col or self.data_matrix.shape[0] == 1:
            if self.data_matrix is not None:
                self.data_matrix = self.data_matrix.transpose()
            if self.error_matrix is not None:
                self.error_matrix = self.error_matrix.transpose()
            if self.label_matrix is not None:
                self.label_matrix = self.label_matrix.transpose()
            if self.colour_matrix is not None:
                self.colour_matrix = self.colour_matrix.transpose()
            if self.transparency_matrix is not None:
                self.transparency_matrix = self.transparency_matrix.transpose()
            self.rows, self.columns = self.columns, self.rows

    def getColour(self, idx, column):
        '''return hatch and colour.'''

        if self.transparency_matrix is not None:
            alpha = self.transparency_matrix[:, column]
        else:
            alpha = None

        # the colour plotting has a problem with arrays, return
        # a list
        if self.colour_matrix is not None:
            color = list(self.colour_matrix[:, column])
            hatch = None
        else:
            hatch, color = self.bar_patterns[idx % len(self.bar_patterns)]
        return hatch, color, alpha

    def addTicks(self, xvals):
        '''add tick marks to plots.'''

        rotation = "horizontal"

        if self.orientation == "vertical":
            if len(self.rows) > 5 or max([len(x) for x in self.rows]) >= 8:
                rotation = "vertical"
                self.rescaleForVerticalLabels(self.rows)

        if self.orientation == 'vertical':
            plt.xticks(
                xvals + self.bar_width / 2., self.rows, rotation=rotation)
        else:
            plt.yticks(
                xvals + self.bar_width / 2., self.rows, rotation=rotation)
            locs, labels = plt.xticks()
            plt.xticks(locs, labels, rotation='vertical')

    def render(self, dataseries, path):

        self.buildMatrices(dataseries)

        self.startPlot()
        plts = []

        xvals = numpy.arange(0, len(self.rows))

        # plot by row
        y, error = 0, None
        for column, header in enumerate(self.columns):

            vals = self.data_matrix[:, column]
            if self.error:
                error = self.error_matrix[:, column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if numpy.isnan(vals[0]) or numpy.isinf(vals[0]):
                vals[0] = 0

            hatch, color, alpha = self.getColour(y, column)
            alpha = 1.0 / (len(plts) + 1)

            if self.bottom_value is not None:
                bottom = float(self.bottom_value)
            else:
                bottom = None

            kwargs = {}
            if self.orientation == 'vertical':
                kwargs['bottom'] = bottom
            else:
                kwargs['left'] = bottom

            plts.append(self.plotf(xvals,
                                   vals,
                                   self.bar_width,
                                   yerr=error,
                                   ecolor="black",
                                   color=color,
                                   hatch=hatch,
                                   alpha=alpha,
                                   log=self.barlog,
                                   **kwargs)[0])

            if self.label and self.label_matrix is not None:
                self.addLabels(xvals, vals,
                               self.label_matrix[:, column])

            y += 1

        self.addTicks(xvals)

        return self.endPlot(plts, self.columns, path)


class InterleavedBarPlot(BarPlot):
    """A plot with interleaved bars.

    This:class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    # always put multiple bars in a plot
    # and multiple data points in a plot
    group_level = -2

    def __init__(self, *args, **kwargs):
        BarPlot.__init__(self, *args, **kwargs)

    def render(self, dataseries, path):

        self.buildMatrices(dataseries)

        self.startPlot()

        width = 1.0 / (len(self.columns) + 1)
        plts, error = [], None
        xvals = numpy.arange(0, len(self.rows))
        offset = width / 2.0

        # plot by row
        row = 0
        for column, header in enumerate(self.columns):

            vals = self.data_matrix[:, column]
            if self.error:
                error = self.error_matrix[:, column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if vals[0] is None or numpy.isnan(vals[0]) or numpy.isinf(vals[0]):
                vals[0] = 0
                if self.error:
                    error[0] = 0
                
            hatch, color, alpha = self.getColour(row, column)

            if self.bottom_value is not None:
                bottom = float(self.bottom_value)
            else:
                bottom = None

            kwargs = {}
            if self.orientation == 'vertical':
                kwargs['bottom'] = bottom
            else:
                kwargs['left'] = bottom

            plts.append(self.plotf(xvals + offset,
                                   vals,
                                   width,
                                   yerr=error,
                                   align="edge",
                                   ecolor="black",
                                   color=color,
                                   hatch=hatch,
                                   alpha=alpha,
                                   log=self.barlog,
                                   **kwargs)[0])

            if self.label and self.label_matrix is not None:
                self.addLabels(xvals + offset,
                               vals,
                               self.label_matrix[:, column])

            offset += width
            row += 1

        self.addTicks(xvals)

        return self.endPlot(plts, self.columns, path)


class StackedBarPlot(BarPlot):

    """A plot with stacked bars.

    This:class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    # always put multiple bars in a plot
    # and multiple data points in a plot
    group_level = -2

    def __init__(self, *args, **kwargs):
        BarPlot.__init__(self, *args, **kwargs)

    def render(self, dataseries, path):

        self.buildMatrices(dataseries)

        self.startPlot()
        plts = []

        xvals = numpy.arange((1.0 - self.bar_width) / 2.,
                             len(self.rows),
                             dtype=numpy.float)
        sums = numpy.zeros(len(self.rows),
                           dtype=numpy.float)

        y, error, is_first = 0, None, True
        legend = []
        colour_offset = 0

        for column, header in enumerate(self.columns):

            # cast to float, otherwise numpy complains
            # about unsafe casting
            vals = numpy.array(self.data_matrix[:, column],
                               dtype=float)
            if self.error:
                error = self.error_matrix[:, column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if vals[0] is None or numpy.isnan(vals[0]) or numpy.isinf(vals[0]):
                vals[0] = 0
                if self.error:
                    error[0] = 0

            kwargs = {}
            if self.orientation == 'vertical':
                kwargs['bottom'] = sums
            else:
                kwargs['left'] = sums

            # do not plot if first value
            if self.first_is_offset and is_first:
                is_first = False
                sums += vals
                y += 1
                # ensure plot starts from 0 unless explicitely given.
                # if self.orientation == 'vertical':
                #     if self.yrange == None: self.yrange = (0,None)
                # else:
                #     if self.xrange == None: self.xrange = (0,None)
                colour_offset = 1
                continue

            hatch, color, alpha = self.getColour(y, column - colour_offset)

            plts.append(self.plotf(xvals,
                                   vals,
                                   self.bar_width,
                                   yerr=error,
                                   color=color,
                                   hatch=hatch,
                                   alpha=alpha,
                                   ecolor="black",
                                   log=self.barlog,
                                   **kwargs)[0])

            if self.label and self.label_matrix is not None:
                self.addLabels(xvals, vals, self.label_matrix[:, column])

            legend.append(header)
            sums += vals
            y += 1

        self.addTicks(xvals)

        return self.endPlot(plts, legend, path)


class DataSeriesPlot(Renderer, Plotter):
    """Plot one or more data series within a single plot.

    The data series is given as a hierachically indexed
    (melted) data series or multiple columns.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    options = Renderer.options + Plotter.options

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        plts, legend = [], []

        self.startPlot()
        if len(dataframe.columns) == 1:
            # in hierarchical indices, get rid of superfluous
            # levels (often these are row numbers)
            if isinstance(dataframe.index,
                          pandas.core.index.MultiIndex):
                todrop = []
                for x, level in enumerate(dataframe.index.levels):
                    if len(level) == len(dataframe.index):
                        todrop.append(x)

                dd = dataframe.reset_index(
                    todrop,
                    drop=True)
                # convert to single-level index
                dd.index = list(map(path2str, dd.index))
            else:
                dd = dataframe

            # convert index to columns
            dd = dd.reset_index()
            assert len(dd.columns) == 2
            dd.columns = ('label', 'value')
            melted = True
        else:
            dd = dataframe
            melted = False

        plts.extend(self.plotData(dd, melted))
        self.updatePlot()

        return self.endPlot(plts, None, path)

    def updatePlot(self):

        ax = plt.gca()
        labels = ax.xaxis.get_majorticklabels()
        if len(labels) > 5:
            for x in labels:
                x.set_rotation(90)


class MultipleSeriesPlot(Renderer, Plotter):

    """Plot data according to different orientations.

    If the dataframe has only a single column, create a single plot
    with row names as keys and the column as values.

    If the dataframe has multiple columns, create one plot
    for each row with the column headers as keys and the
    row as values.

    """
    options = Renderer.options + Plotter.options

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        blocks = ResultBlocks()
        if len(dataframe.columns) == 1:
            keys = tuple(dataframe.index)
            values = tuple(dataframe.iloc[:, 0])
            blocks.extend(self.plot(keys, values, path))
        else:
            for title, row in dataframe.iterrows():
                row = row[row.notnull()]
                keys = tuple(row.index)
                values = tuple(row)
                blocks.extend(
                    self.plot(keys, values,
                              title + path))

        return blocks

    def updatePlot(self, legend):
        return


class PlotByRow(Renderer, Plotter):

    '''Create multiple plots from a dataframe in row-wise fashion.

    Currently not used by any subclass.
    '''

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        blocks = ResultBlocks()
        for title, row in dataframe.iterrows():
            row = row[row.notnull()]
            values = row.tolist()
            headers = list(row.index)

            blocks.extend(self.plot(headers, values, path))

        return blocks


class PiePlot(MultipleSeriesPlot):
    """A pie chart.

    If *pie-first-is-total* is set, the first entry
    is assumed to be the total and all the other values
    are subtracted. It is renamed by the value of *pie-first-is-total*.
    """
    options = TableMatrix.options + Plotter.options +\
        (('pie-min-percentage', directives.unchanged),
         ('pie-first-is-total', directives.unchanged),)

    # Do not group data
    group_level = 'force-none'

    def __init__(self, *args, **kwargs):
        MultipleSeriesPlot.__init__(self, *args, **kwargs)

        self.mPieMinimumPercentage = float(kwargs.get("pie-min-percentage", 0))

        self.mFirstIsTotal = kwargs.get("pie-first-is-total", None)

        # store a list of sorted headers to ensure the same sort order
        # in all plots.
        self.sorted_keys = odict()

    def plot(self, keys, values, path):

        # If there is only a single column, keys will be
        # the sample, not the category
        if len(keys) == 1:
            if self.mFirstIsTotal:
                keys = [self.mFirstIsTotal]

        for x in keys:
            if x not in self.sorted_keys:
                self.sorted_keys[x] = len(self.sorted_keys)

        sorted_vals = [0] * len(self.sorted_keys)

        for key, value in zip(keys, values):
            if value < self.mPieMinimumPercentage:
                sorted_vals[self.sorted_keys[key]] = 0
                if "other" not in self.sorted_keys:
                    self.sorted_keys["other"] = len(self.sorted_keys)
                    sorted_vals.append(0)
                sorted_vals[self.sorted_keys["other"]] += value
            else:
                sorted_vals[self.sorted_keys[key]] = value

        labels = list(self.sorted_keys.keys())

        self.startPlot()

        if sum(sorted_vals) == 0:
            return self.endPlot(None, None, path)

        # subtract others from total - rest
        if self.mFirstIsTotal and len(sorted_vals) > 1:
            sorted_vals[0] -= sum(sorted_vals[1:])
            if sorted_vals[0] < 0:
                raise ValueError(
                    "option first-is-total used, but first (%i) < rest (%i)" %
                    (sorted_vals[0] + sum(sorted_vals[1:]),
                     sum(sorted_vals[1:])))
            labels[0] = self.mFirstIsTotal

        return self.endPlot(plt.pie(sorted_vals, labels=labels),
                            None,
                            path)


class TableMatrixPlot(TableMatrix, PlotterMatrix):

    """Render a matrix as a matrix plot.
    """
    options = TableMatrix.options + PlotterMatrix.options

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs)
        PlotterMatrix.__init__(self, *args, **kwargs)

    def render(self, work, path):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix(work)
        self.debug("building matrix finished")
        return self.plot(matrix, rows, columns, path)

# for compatibility
MatrixPlot = TableMatrixPlot


class NumpyMatrixPlot(NumpyMatrix, PlotterMatrix):

    """Render a matrix as a matrix plot.
    """
    options = NumpyMatrix.options + PlotterMatrix.options

    def __init__(self, *args, **kwargs):
        NumpyMatrix.__init__(self, *args, **kwargs)
        PlotterMatrix.__init__(self, *args, **kwargs)

    def render(self, work, path):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix(work)

        self.debug("building matrix finished")
        return self.plot(matrix, rows, columns, path)


class HintonPlot(TableMatrix, PlotterHinton):

    """Render a matrix as a hinton plot.

    Draws a Hinton diagram for visualizing a weight matrix.

    The size of a box reflects the weight.

    This class adds the following options to the:term:`report` directive:

    :term:`colours`: colour boxes according to value.

    """
    options = TableMatrix.options + PlotterHinton.options +\
        (('colours', directives.unchanged),
         )

    # column to use for error bars
    colour = None

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs)
        PlotterHinton.__init__(self, *args, **kwargs)

        self.colour = kwargs.get("colour", None)

        if self.colour:
            self.nlevels += 1

    def render(self, work, path):
        """render the data."""

        matrix, rows, columns = self.buildMatrices(work)
        return self.plot(matrix, rows, columns, path)


class GalleryPlot(PlotByRow):

    '''Plot an image.
    '''

    options = Renderer.options + Plotter.options

    nlevels = 1

    def __init__(self, *args, **kwargs):
        PlotByRow.__init__(self, *args, **kwargs)

    def plot(self, headers, values, path):

        blocks = ResultBlocks()
        dataseries = dict(list(zip(headers, values)))
        try:
            # return value is a series
            filename = dataseries['filename']
        except KeyError:
            self.warn(
                "no 'filename' key in path %s" % (path2str(path)))
            return blocks

        rst_text = '''.. figure:: %(filename)s
'''

        # Warning: the link here will be invalid
        # if a report is moved.
        rst_link = '''* `%(title)s <%(absfn)s>`_
'''

        plts = []

        absfn = os.path.abspath(filename)
        title = os.path.basename(filename)

        # do not render svg images
        if filename.endswith(".svg"):
            return ResultBlocks(ResultBlock(text=rst_text % locals(),
                                            title=title))
        # do not render pdf images
        elif filename.endswith(".pdf"):
            return ResultBlocks(ResultBlock(text=rst_link % locals(),
                                            title=title))
        else:
            self.startPlot()
            try:
                data = plt.imread(filename)
            except IOError:
                raise ValueError(
                    "file format for file '%s' not recognized" % filename)

            ax = plt.gca()
            ax.frameon = False
            ax.axison = False

            # remove excess space around the image
            plt.tight_layout(pad=0)

            # Create a plot which the same shape as the original plot
            im_aspect = float(data.shape[0]) / float(data.shape[1])
            plt_size = self.mCurrentFigure.get_size_inches()
            self.mCurrentFigure.set_figheight(plt_size[0] * im_aspect)

            plts.append(plt.imshow(data))
            ax.set_position([0, 0, 1, 1])

        if "name" in dataseries:
            path = dataseries['name']

        blocks = ResultBlocks(ResultBlock("\n".join(
            ("#$mpl %i$#" % (self.mFigure),
             "",
             "",
             )),
            title=path2str(path)))

        return blocks


class ScatterPlot(Renderer, Plotter):

    """Scatter plot.

    The different tracks will be displayed with different colours.

    This:class:`Renderer` requires two levels:
    track[dict] / coords[dict]

    :regression:
    int

       add linear regression function of a certain degree
       (straight line is degree 1).

    """
    options = Renderer.options + Plotter.options +\
        (('regression', directives.unchanged),
         )

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        # plt.scatter does not permitting setting
        # options in rcParams - hence the parameters
        # are parsed explicitely here

        self.markersize = self.mMPLRC.get(
            "lines.markersize",
            plt.rcParams.get("lines.markersize", 6))

        self.markeredgewidth = self.mMPLRC.get(
            "lines.markeredgewith",
            plt.rcParams.get("lines.markeredgewidth",
                             0.5))

        self.regression = int(kwargs.get("regression", 0))

    def render(self, dataframe, path):

        nplotted = 0

        plts, legend = [], []
        xlabels, ylabels = [], []

        columns = dataframe.columns

        if len(columns) < 2:
            raise ValueError(
                'require at least two columns, got %i' % len(columns))

        level = Utils.getGroupLevels(dataframe)
        xcolumn = columns[0]
        started = False

        for key, work in dataframe.groupby(
                level=level):
            for column in columns[1:]:

                # remove missing data points
                xvalues, yvalues = Stats.filterMissing(
                    (work[xcolumn], work[column]))

                # remove columns with all NaN
                if len(xvalues) == 0 or len(yvalues) == 0:
                    continue

                if not started:
                    self.startPlot()
                    started = True

                marker = self.format_markers[
                    nplotted % len(self.format_markers)]
                color = self.format_colors[
                    nplotted % len(self.format_colors)]

                # plt.scatter does not permitting setting
                # options in rcParams, so all is explict
                plts.append(plt.scatter(
                    xvalues,
                    yvalues,
                    marker=marker,
                    c=color,
                    linewidths=self.markeredgewidth,
                    s=self.markersize))

                label = path2str(key) + "/" + path2str(column)
                legend.append(label)

                if self.regression:
                    coeffs = numpy.polyfit(xvalues, yvalues, self.regression)
                    p = numpy.poly1d(coeffs)
                    svals = sorted(xvalues)
                    plts.append(plt.plot(svals,
                                         [p(x) for x in svals],
                                         c=color,
                                         marker='None'))

                    legend.append("regression %s" % label)

                nplotted += 1

        plt.xlabel(xcolumn)
        plt.ylabel(":".join(map(str, columns[1:])))

        return self.endPlot(plts, legend, path)


class ScatterPlotWithColor(ScatterPlot):

    """Scatter plot with individual colors for each dot.

    This class adds the following options to the:term:`report` directive:

:term:`colorbar-format`: numerical format for the colorbar.

:term:`palette`: numerical format for the colorbar.

:term:`zrange`: restrict plot a part of the z-axis.

    This:class:`Renderer` requires one level:

    coords[dict]
    """
    options = Renderer.options + Plotter.options +\
        (('palette', directives.unchanged),
         ('reverse-palette', directives.flag),
         ('colorbar-format', directives.unchanged))

    nlevels = 2

    def __init__(self, *args, **kwargs):
        ScatterPlot.__init__(self, *args, **kwargs)

        try:
            self.mBarFormat = kwargs["colorbar-format"]
        except KeyError:
            self.mBarFormat = "%1.1f"

        try:
            self.mPalette = kwargs["palette"]
        except KeyError:
            self.mPalette = "jet"

        self.mReversePalette = "reverse-palette" in kwargs

    def render(self, dataframe, path):

        self.startPlot()

        plts = []

        if self.mPalette:
            if self.mReversePalette:
                color_scheme = eval("plt.cm.%s_r" % self.mPalette)
            else:
                color_scheme = eval("plt.cm.%s" % self.mPalette)
        else:
            color_scheme = None

        nplotted = 0

        plts, legend = [], []
        xlabels, ylabels = [], []

        assert len(dataframe.columns) >= 3, \
            "expected at least three columns, got %i: %s" % (dataframe.columns)

        xcolumn, ycolumn, zcolumn = dataframe.columns[:3]

        xvalues, yvalues, zvalues = dataframe[xcolumn], dataframe[ycolumn], \
            dataframe[zcolumn]

        xvals, yvals, zvals = Stats.filterMissing((xvalues, yvalues, zvalues))

        if len(xvalues) == 0 or len(yvalues) == 0 or len(zvalues) == 0:
            raise ValueError("no data")

        if self.zrange:
            vmin, vmax = self.zrange
            zvals = numpy.array(zvals)
            zvals[zvals < vmin] = vmin
            zvals[zvals > vmax] = vmax
        else:
            vmin, vmax = None, None

        marker = self.format_markers[nplotted % len(self.format_markers)]

        # plt.scatter does not permitting setting
        # options in rcParams, so all is explict
        plts.append(plt.scatter(xvalues,
                                yvalues,
                                marker=marker,
                                s=self.markersize,
                                c=zvalues,
                                linewidths=self.markeredgewidth,
                                cmap=color_scheme,
                                vmax=vmax,
                                vmin=vmin))

        nplotted += 1

        xlabels.append(xcolumn)
        ylabels.append(ycolumn)
        cb = plt.colorbar(format=self.mBarFormat)
        cb.ax.set_xlabel(zcolumn)

        plt.xlabel(":".join(set(xlabels)))
        plt.ylabel(":".join(set(ylabels)))

        return self.endPlot(plts, None, path)


class VennPlot(Renderer, Plotter):

    '''plot a two and three circle venn diagramm.

    This:term:`renderer` plots a Venn diagramm.

    The dictionary should contain the elements
    * ('10', '01', and '11') for a two-circle Venn diagram.
    * ('100', '010', '110', '001', '101', '011', '111')
      for a three-circle Venn diagram.

    When plotting, the function looks for the first 3 or 7 element dictionary
    and the first 3 or 7 element list.

    data[dict]
    '''

    options = Renderer.options + Plotter.options

    # no grouping
    group_level = -1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        if matplotlib_venn is None:
            raise ValueError("library matplotlib_venn not available")

        if "names" not in dataframe.index.names:
            raise ValueError(
                "expected 'names' in index, got %s" %
                str(dataframe.index.names))

        keys = tuple(dataframe.index.get_level_values('names'))
        plts = []
        self.startPlot()

        for column in dataframe.columns:

            values = tuple(dataframe[column])
            subsets = dict(list(zip(keys, values)))

            if "labels" in subsets:
                setlabels = subsets["labels"]
                del subsets["labels"]

            if subsets is None:
                self.warn(
                    "no suitable data for Venn diagram at %s" % str(path))
                return self.endPlot(plts, None, path)

            if len(subsets) == 3:
                if 0 in (subsets['10'], subsets['01']):
                    self.warn("empty sets for Venn diagram at %s" % str(path))
                    return self.endPlot(plts, None, path)

                if setlabels:
                    if len(setlabels) != 2:
                        raise ValueError("require two labels, got %i" %
                                         len(setlabels))
                plts.append(matplotlib_venn.venn2(subsets,
                                                  set_labels=setlabels))
            elif len(subsets) == 7:
                if 0 in (subsets['100'], subsets['010'], subsets['001']):
                    self.warn("empty sets for Venn diagram at %s" % str(path))
                    return self.endPlot(plts, None, path)

                if setlabels:
                    if len(setlabels) != 3:
                        raise ValueError("require three labels, got %i" %
                                         len(setlabels))
                plts.append(matplotlib_venn.venn3(subsets,
                                                  set_labels=setlabels))
            else:
                raise ValueError(
                    "require 3 or 7 values for a Venn diagramm, got %i" %
                    len(subsets))

        return self.endPlot(plts, None, path)
