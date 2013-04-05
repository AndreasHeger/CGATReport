"""Mixin classes for Renderers that plot.
"""

import os, sys, re, math, itertools

import matplotlib
matplotlib.use('Agg', warn = False)
# This does not work:
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own matplotlibrc.

import matplotlib.colors
import matplotlib.pyplot as plt

# Python 3 Compatibility
try: import matplotlib_venn
except ImportError: matplotlib_venn = None

import numpy 

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReportPlugins.Renderer import Renderer, NumpyMatrix, TableMatrix
from SphinxReport.DataTree import path2str
from collections import OrderedDict as odict
from SphinxReport import Utils, DataTree, Stats

from docutils.parsers.rst import directives

# see http://messymind.net/2012/07/making-matplotlib-look-like-ggplot/    
def rstyle(ax):
    """Styles an axes to appear like ggplot2
    Must be called after all plot and axis manipulation operations have been carried out (needs to know final tick spacing)
    """
    #set the style of the major and minor grid lines, filled blocks
    ax.grid(True, 'major', color='w', linestyle='-', linewidth=1.4)
    ax.grid(True, 'minor', color='0.92', linestyle='-', linewidth=0.7)
    ax.patch.set_facecolor('0.85')
    ax.set_axisbelow(True)
   
    xticks = plt.xticks()
    yticks = plt.yticks()
    #set minor tick spacing to 1/2 of the major ticks
    if len(xticks) > 2:
        ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator( (xticks[0][1]-xticks[0][0]) / 2.0 ))
    if len(yticks) > 2:
        ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator( (yticks[0][1]-yticks[0][0]) / 2.0 ))
   
    #remove axis border
    for child in ax.get_children():
        if isinstance(child, matplotlib.spines.Spine):
            child.set_alpha(0)
       
    #restyle the tick lines
    for line in ax.get_xticklines() + ax.get_yticklines():
        line.set_markersize(5)
        line.set_color("gray")
        line.set_markeredgewidth(1.4)
   
    #remove the minor tick lines    
    for line in ax.xaxis.get_ticklines(minor=True) + ax.yaxis.get_ticklines(minor=True):
        line.set_markersize(0)
   
    #only show bottom left ticks, pointing out of axis
    matplotlib.rcParams['xtick.direction'] = 'out'
    matplotlib.rcParams['ytick.direction'] = 'out'
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
      
    if ax.legend_ != None:
        lg = ax.legend_
        lg.get_frame().set_linewidth(0)
        lg.get_frame().set_alpha(0.5)
       
def rhist(ax, data, **keywords):
    """Creates a histogram with default style parameters to look like ggplot2
    Is equivalent to calling ax.hist and accepts the same keyword parameters.
    If style parameters are explicitly defined, they will not be overwritten
    """
   
    defaults = {
                'facecolor' : '0.3',
                'edgecolor' : '0.28',
                'linewidth' : '1',
                'bins' : 100
                }
   
    for k, v in list(defaults.items()):
        if k not in keywords: keywords[k] = v
   
    return ax.hist(data, **keywords)


def rbox(ax, data, **keywords):
    """Creates a ggplot2 style boxplot, is eqivalent to calling ax.boxplot with the following additions:
   
    Keyword arguments:
    colors -- array-like collection of colours for box fills
    names -- array-like collection of box names which are passed on as tick labels

    """

    hasColors = 'colors' in keywords

    if hasColors:
        colors = keywords['colors']
        keywords.pop('colors')
       
    if 'names' in keywords:
        ax.tickNames = plt.setp(ax, xticklabels=keywords['names'] )
        keywords.pop('names')
   
    bp = ax.boxplot(data, **keywords)
    pylab.setp(bp['boxes'], color='black')
    pylab.setp(bp['whiskers'], color='black', linestyle = 'solid')
    pylab.setp(bp['fliers'], color='black', alpha = 0.9, marker= 'o', markersize = 3)
    pylab.setp(bp['medians'], color='black')
   
    numBoxes = len(data)
    for i in range(numBoxes):
        box = bp['boxes'][i]
        boxX = []
        boxY = []
        for j in range(5):
          boxX.append(box.get_xdata()[j])
          boxY.append(box.get_ydata()[j])
        boxCoords = list(zip(boxX,boxY))
       
        if hasColors:
            boxPolygon = Polygon(boxCoords, facecolor = colors[i % len(colors)])
        else:
            boxPolygon = Polygon(boxCoords, facecolor = '0.95')
           
        ax.add_patch(boxPoly)

    return bp


def parseRanges(r):
    '''given a string in the format "x,y", 
    return a tuple of values (x,y).

    missing values are set to None.
    '''

    if not r: return r
    r = [ x.strip() for x in r.split(",")]
    if r[0] == "": r[0] = None
    else: r[0] = float(r[0])
    if r[1] == "": r[1] = None
    else: r[1] = float(r[1])
    return r

class Plotter(object):
    """Base class for Renderers that do simple 2D plotting.

    This mixin class provides convenience function for :class:`Renderer.Renderer`
    classes that do 2D plotting.

    The base class takes care of counting the plots created,
    provided that the methods :meth:`startPlot` and :meth:`endPlot`
    are called appropriately. It then inserts the appropriate place holders.

    This class adds the following options to the :term:`report` directive:

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

    ## maximum number of rows per column. If there are more,
    ## the legend is split into multiple columns
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
        )

    mColors = "bgrcmk"
    mSymbols = ["g-D","b-h","r-+","c-+","m-+","y-+","k-o","g-^","b-<","r->","c-D","m-h"]
    mMarkers = "so^>dph8+x"
    mPatterns = [None, '/','\\','|','-','+','x','o','O','.','*']

    use_rstyle = True

    def __init__(self, *args, **kwargs ):
        """parse option arguments."""

        self.mFigure = 0

        self.logscale = kwargs.get("logscale", None )
        self.title = kwargs.get("title", None )
        self.add_title = "add-title" in kwargs
        self.xlabel = kwargs.get("xtitle", None )
        self.ylabel = kwargs.get("ytitle", None )
        self.functions = kwargs.get("function", None )
        self.vline = kwargs.get("vline", None )

        if self.functions:
            if "," in self.functions: self.functions = self.functions.split(",")
            else: self.functions = [self.functions]
            
        # substitute '-' in SphinxReport-speak for ' ' in matplotlib speak
        self.legend_location = re.sub("-", " ", kwargs.get("legend-location", "outer-top"))

        self.width = kwargs.get("width", 0.50 )
        self.xrange = parseRanges(kwargs.get("xrange", None ))
        self.yrange = parseRanges(kwargs.get("yrange", None ))
        self.zrange = parseRanges(kwargs.get("zrange", None ))

        self.xformat = kwargs.get("xformat", None )
        self.yformat = kwargs.get("yformat", None )

        def setupMPLOption( key ):
            options = {}
            try: 
                for k in kwargs[ key ].split(";"):
                    key,val = k.split("=")
                    # convert unicode to string
                    try:
                        options[str(key)] = eval(val)
                    except NameError:
                        options[str(key)] = val
            except KeyError: 
                pass
            return options

        self.mMPLFigureOptions = setupMPLOption( "mpl-figure" )
        self.mMPLLegendOptions = setupMPLOption( "mpl-legend" )
        self.mMPLSubplotOptions = setupMPLOption( "mpl-subplot" )
        self.mMPLRC = setupMPLOption( "mpl-rc" )

    def startPlot( self, **kwargs ):
        """prepare everything for a plot.
        
        returns the current figure.
        """

        self.mFigure +=1 

        # go to defaults
        matplotlib.rcdefaults()

        # set parameters
        if self.mMPLRC:
            self.debug( "extra plot options: %s" % str(self.mMPLRC) )
            matplotlib.rcParams.update(self.mMPLRC )
        
        self.mCurrentFigure = plt.figure( num = self.mFigure, **self.mMPLFigureOptions )

        if self.title:  plt.title( self.title )

        return self.mCurrentFigure

    def wrapText( self, text, cliplen = 20, separators = " :_" ):
        """wrap around text using the mathtext.

        Currently this subroutine uses the \frac 
        directive, so it is not pretty.
        returns the wrapped text."""
        
        # split txt into two equal parts trying
        # a list of separators
        newtext = []
        for txt in text:
            t = len(txt)
            if t > cliplen:
                for s in separators:
                    parts = txt.split( s )
                    if len(parts) < 2 : continue
                    c = 0
                    tt = t // 2
                    # collect first part such that length is 
                    # more than half
                    for x, p in enumerate( parts ):
                        if c > tt: break
                        c += len(p)

                    # accept if a good split (better than 2/3)
                    if float(c) / t < 0.66:
                        newtext.append( r"$\mathrm{\frac{ %s }{ %s }}$" % \
                                            ( s.join(parts[:x]), s.join(parts[x:])))
                        break
            else:
                newtext.append(txt)
        return newtext

    def endPlot( self, plts, legends, path ):
        """close plots.

        This method performs common post-processing options on matplotlib
        rendered plots:

           * rescaling the axes
           * legend placement
           * adding a function to the plot

        returns blocks of restructured text with place holders for the 
        figure.
        """

        if not plts: return ResultBlocks()

        ax = plt.gca()
        # set logscale before the xlim, as it re-scales the plot.
        if self.logscale:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            if "x" in self.logscale:
                try:
                    ax.set_xscale('log')
                    # rescale: log plots does not autoscale well if negative values
                    # scale manually - needs to be overridden by the user if small
                    # values are to be expected
                    if xlim[0] < 0:
                        ax.set_xlim( (0.01, None ))
                except OverflowError:
                    ax.set_xscale('linear')

            if "y" in self.logscale:
                try:
                    ax.set_yscale('log')
                    # rescale: log plots does not autoscale well if negative values
                    # scale manually - needs to be overridden by the user if small
                    # values are to be expected
                    if ylim[0] < 0:
                        ax.set_ylim( (0.01, None ))
                except OverflowError:
                    ax.set_yscale('linear')

            ax.relim()

        if self.xrange:
            plt.xlim( self.xrange )
        if self.yrange:
            plt.ylim( self.yrange )

        if self.functions:
            xstart, xend = ax.get_xlim()
            increment = (xend - xstart) / 100.0
            for function in self.functions:
                f = eval("lambda x: %s" % function )
                print(locals())
                xvals = numpy.arange( xstart, xend, increment)
                yvals = [ f(x) for x in xvals ]
                plt.plot( xvals, yvals )

        if self.vline:
            ystart, yend = ax.get_ylim()
            lines = list(map(int, self.vline.split(",") ))
            ax.vlines( lines, ystart, yend )

        # add labels and titles
        if self.add_title: 
            plt.suptitle( DataTree.path2str( path ) )

        if self.xlabel: plt.xlabel( self.xlabel )
        if self.ylabel: plt.ylabel( self.ylabel )

        # change x/y axis formatter
        if self.xformat:
            if self.xformat.startswith('date'):
                xlim = ax.get_xlim()
                if xlim[0] < 1:
                    raise ValueError( "date value out of range - needs to larger than 1")

                ax.xaxis_date()
                loc = matplotlib.dates.AutoDateLocator()
                ax.xaxis.set_major_locator( loc )
                fmt = self.xformat[5:].strip()
                if not fmt: fmt = '%Y-%m-%d'
                ax.xaxis.set_major_formatter(
                    matplotlib.dates.AutoDateFormatter(loc,
                                                       defaultfmt = fmt ))

        if self.yformat:
            if self.yformat.startswith('date'):
                ylim = ax.get_ylim()
                if ylim[0] < 1:
                    raise ValueError( "date value out of range - needs to larger than 1")

                ax.yaxis_date()
                loc = matplotlib.dates.AutoDateLocator()
                ax.yaxis.set_major_locator( loc )
                fmt = self.yformat[5:].strip()
                if not fmt: fmt = '%Y-%m-%d'
                ax.yaxis.set_major_formatter(
                    matplotlib.dates.AutoDateFormatter(loc,
                                                       defaultfmt = fmt))

        blocks = ResultBlocks( ResultBlock( "\n".join( 
                    ("#$mpl %i$#" % (self.mFigure), "")), title = DataTree.path2str(path) ) )

        legend = None
        maxlen = 0

        # In matplotlib version < 1.1, the output of plotting was 
        # a single element. In later versions, the output is a tuple
        # so take first element.
        if type(plts[0]) in (tuple, list):
            plts = [ x[0] for x in plts ]

        if self.legend_location != "none" and plts and legends:


            maxlen = max( [ len(x) for x in legends ] )
            # legends = self.wrapText( legends )

            assert len(plts) == len(legends)
            if self.legend_location.startswith( "outer" ):
                legend = outer_legend( plts, legends, loc = self.legend_location )
            else:
                legend = plt.figlegend( plts, 
                                        legends,
                                        loc = self.legend_location,
                                        **self.mMPLLegendOptions )

        if self.legend_location == "extra" and legends:

            blocks.append( ResultBlock( "\n".join( ("#$mpl %i$#" % self.mFigure, "")), "legend" ) )
            self.mFigure += 1
            legend = plt.figure( self.mFigure, **self.mMPLFigureOptions )
            lx = legend.add_axes( (0.1, 0.1, 0.9, 0.9) )
            lx.set_title( "Legend" )
            lx.set_axis_off()
            plt.setp( lx.get_xticklabels(), visible=False)
            if not plts:
                plts = []
                for x in legends:
                    plts.append( plt.plot( (0,), (0,) ) )

            lx.legend( plts, legends, 
                       'center left',
                       ncol = max(1,int(math.ceil( float( len(legends) / self.mLegendMaxRowsPerColumn ) ) )),
                       **self.mMPLLegendOptions )

        if self.use_rstyle:
            rstyle( ax )

        # smaller font size for large legends
        if legend and maxlen > self.mMaxLegendSize:
            ltext = legend.get_texts() # all the text.Text instance in the legend
            plt.setp(ltext, fontsize='small') 

        return blocks

    def rescaleForVerticalLabels( self, labels, offset = 0.02, cliplen = 6 ):
        """rescale current plot so that vertical labels are displayed properly.

        In some plots the labels are clipped if the labels are vertical labels on the X-axis.
        This is a heuristic hack and is not guaranteed to always work.
        """
        # rescale plotting area if labels are more than 6 characters
        if len(labels) == 0: return

        maxlen = max( [ len(x) for x in labels ] )
        if maxlen > cliplen:
            currentAxes = plt.gca()
            currentAxesPos = currentAxes.get_position()

            # scale plot by 2% for each extra character
            # scale at most 30% as otherwise the plot will
            # become illegible (and matplotlib might crash)
            offset = min(0.3, offset * (maxlen- cliplen) )

            # move the x-axis up
            currentAxes.set_position((currentAxesPos.xmin,
                                      currentAxesPos.ymin + offset,
                                      currentAxesPos.width,
                                      currentAxesPos.height -offset))

class PlotterMatrix(Plotter):
    """Plot a matrix.

    This mixin class provides convenience function for :class:`Renderer.Renderer`
    classes that plot matrices.
    
    This class adds the following options to the :term:`report` directive:
    
       :term:`colorbar-format`: numerical format for the colorbar.

       :term:`palette`: numerical format for the colorbar.

       :term:`reverse-palette`: invert palette

       :term:`max-rows`: maximum number of rows per plot

       :term:`max-cols`: maximum number of columns per plot
       
    """

    mFontSize = 8

    # after # characters, split into two
    # lines
    mSplitHeader = 20
    mFontSizeSplit = 8

    # separators to use to split text
    mSeparators = " :_"

    # Do not use R style for plotting.
    use_rstyle = False

    options = Plotter.options +\
        ( ('palette', directives.unchanged),
          ('reverse-palette', directives.flag),
          ('max-rows', directives.unchanged),
          ('max-cols', directives.unchanged),
          ('colorbar-format', directives.unchanged),
          ('nolabel-rows', directives.flag ),
          ('nolabel-cols', directives.flag ),
          )

    def __init__(self, *args, **kwargs ):
        Plotter.__init__(self, *args, **kwargs)

        self.mBarFormat = kwargs.get( "colorbar-format", "%1.1f" )
        self.mPalette = kwargs.get("palette", "jet" )
        self.mMaxRows = int(kwargs.get("max-rows", 20))
        self.mMaxCols = int(kwargs.get("max-cols", 20))

        self.mReversePalette = "reverse-palette" in kwargs
        self.label_rows = "nolabel-rows" not in kwargs
        self.label_cols = "nolabel-cols" not in kwargs

    def addColourBar( self ):
        plt.colorbar( format = self.mBarFormat)        

    def buildWrappedHeaders( self, headers ):
        """build headers. Long headers are split using
        the \frac mathtext directive (mathtext does not
        support multiline equations. 

        This method is currently not in use.

        returns (fontsize, headers)
        """

        fontsize = self.mFontSize
        maxlen = max( [ len(x) for x in headers ] )

        if maxlen > self.mSplitHeader:
            h = []
            fontsize = self.mFontSizeSplit

            for header in headers:
                if len(header) > self.mSplitHeader:
                    # split txt into two equal parts trying
                    # a list of separators
                    t = len(header)
                    for s in self.mSeparators:
                        parts= header.split( s )
                        if len(parts) < 2 : continue
                        c = 0
                        tt = t // 2
                        ## collect first part such that length is 
                        ## more than half
                        for x, p in enumerate( parts ):
                            if c > tt: break
                            c += len(p)

                        # accept if a good split (better than 2/3)
                        if float(c) / t < 0.66:
                            h.append( r"$\mathrm{\frac{ %s }{ %s }}$" % \
                                          ( s.join(parts[:x]), s.join(parts[x:])))
                            break
                    else:
                        h.append(header)
                else:
                    h.append(header)
            headers = h
            
        return fontsize, headers

    def plotMatrix( self, matrix, row_headers, col_headers, vmin, vmax, color_scheme = None):

        self.debug("plot matrix started")

        # when matrix is very different from square matrix
        # adjust figure size
        # better would be to move the axes as well to the left of
        # the figure.
        if len(row_headers) > 2 * len(col_headers):
            r = float(len(row_headers)) /  len(col_headers) * 0.5
            w,h = self.mCurrentFigure.get_size_inches()
            self.mCurrentFigure.set_size_inches( w, h * r )
        elif len(col_headers) > 2 * len(row_headers):
            r = float(len(col_headers)) /  len(row_headers)
            w,h = self.mCurrentFigure.get_size_inches() * 0.5
            self.mCurrentFigure.set_size_inches( w * r, h  )

        plot = plt.imshow(matrix,
                          cmap=color_scheme,
                          origin='lower',
                          vmax = vmax,
                          vmin = vmin,
                          interpolation='nearest')

            
        # offset=0: x=center,y=center
        # offset=0.5: y=top/x=right
        offset = 0.0

        if self.label_rows:
            row_headers = [ str(x) for x in row_headers ]
            yfontsize, row_headers = self.mFontSize, row_headers
            plt.yticks( [ offset + y for y in range(len(row_headers)) ],
                        row_headers,
                        fontsize=yfontsize )

        if self.label_cols:
            col_headers = [ str(x) for x in col_headers ]
            xfontsize, col_headers = self.mFontSize, col_headers
            plt.xticks( [ offset + x for x in range(len(col_headers)) ],
                        col_headers,
                        rotation="vertical",
                        fontsize=xfontsize )


        self.debug("plot matrix finished")            

        return plot

    def plot( self,  matrix, row_headers, col_headers, path ):
        '''plot matrix. 

        Large matrices are split into several plots.
        '''

        self.debug("plot started")

        self.startPlot()

        nrows, ncols = matrix.shape
        if self.zrange:
            vmin, vmax = self.zrange
            if vmin == None: vmin = matrix.min()
            if vmax == None: vmax = matrix.max()
            matrix[ matrix < vmin ] = vmin
            matrix[ matrix > vmax ] = vmax
        else:
            vmin, vmax = None, None

        if self.mPalette:
            try:
                if self.mReversePalette:
                    color_scheme = eval( "plt.cm.%s_r" % self.mPalette)                    
                else:
                    color_scheme = eval( "plt.cm.%s" % self.mPalette)
            except AttributeError:
                raise ValueError("unknown palette '%s'" % self.mPalette )
        else:
            color_scheme = None

        plots, labels = [], []

        split_row = self.mMaxRows > 0 and nrows > self.mMaxRows
        split_col = self.mMaxCols > 0 and ncols > self.mMaxCols


        if (split_row and split_col) or not (split_row or split_col):
            self.debug("not splitting matrix")
            # do not split small or symmetric matrices

            cax = self.plotMatrix( matrix, row_headers, col_headers, vmin, vmax, color_scheme )
            plots.append( cax )
            # plots, labels = None, None
            self.rescaleForVerticalLabels( col_headers, cliplen = 12 )
            self.addColourBar()

            if False:
                plot_nrows = int(math.ceil( float(nrows) / self.mMaxRows ))
                plot_ncols = int(math.ceil( float(ncols) / self.mMaxCols ))
                new_row_headers = [ "R%s" % (x + 1) for x in range(len(row_headers))]
                new_col_headers = [ "C%s" % (x + 1) for x in range(len(col_headers))]
                nplot = 1
                for row in range(plot_nrows):
                    for col in range(plot_ncols):
                        plt.subplot( plot_nrows, plot_ncols, nplot )
                        nplot += 1
                        row_start = row * self.mMaxRows
                        row_end = row_start+min(plot_nrows,self.mMaxRows)
                        col_start = col * self.mMaxRows
                        col_end = col_start+min(plot_ncols,self.mMaxCols)
                        self.plotMatrix( matrix[row_start:row_end,col_start:col_end], 
                                         new_row_headers[row_start:row_end], 
                                         new_col_headers[col_start:col_end], 
                                         vmin, vmax,
                                         color_scheme )

                labels = ["%s: %s" % x for x in zip( new_headers, row_headers) ]
                self.legend_location = "extra"
                plt.subplots_adjust( **self.mMPLSubplotOptions )

        elif split_row:
            self.debug("splitting matrix at row")

            if not self.zrange:
                vmin, vmax = matrix.min(), matrix.max()
            nplots = int(math.ceil( float(nrows) / self.mMaxRows ))
            new_headers = [ "%s" % (x + 1) for x in range(len(row_headers))]
            for x in range(nplots):
                plt.subplot( 1, nplots, x+1 )
                start = x * self.mMaxRows
                end = start+min(nrows,self.mMaxRows)
                cax = self.plotMatrix( matrix[start:end,:], 
                                       new_headers[start:end], 
                                       col_headers, 
                                       vmin, vmax,
                                       color_scheme )
                plots.append( cax )
            # labels = ["%s: %s" % x for x in zip( new_headers, row_headers) ] 

            self.legend_location = "extra"
            plt.subplots_adjust( **self.mMPLSubplotOptions )
            self.addColourBar()

        elif split_col:
            self.debug("splitting matrix at column")
            if not self.zrange:
                vmin, vmax = matrix.min(), matrix.max()
            nplots = int(math.ceil( float(ncols) / self.mMaxCols ))
            new_headers = [ "%s" % (x + 1) for x in range(len(col_headers))]
            for x in range(nplots):
                plt.subplot( nplots, 1, x+1 )
                start = x * self.mMaxCols
                end = start+min(ncols,self.mMaxCols)
                cax = self.plotMatrix( matrix[:,start:end], 
                                       row_headers, 
                                       new_headers[start:end], 
                                       vmin, vmax,
                                       color_scheme ) 
                plots.append( cax )
            # labels = ["%s: %s" % x for x in zip( new_headers, col_headers) ] 

            self.legend_location = "extra"
            plt.subplots_adjust( **self.mMPLSubplotOptions )
            self.addColourBar()

        self.debug("plot finished")

        return self.endPlot( plots, labels, path )

class PlotterHinton(PlotterMatrix):
    '''plot a hinton diagram.

    Draws a Hinton diagram for visualizing a weight matrix. 

    The size of a box reflects the weight.

    Taken from http://www.scipy.org/Cookbook/Matplotlib/HintonDiagrams
    and modified to add colours, labels, etc.
    '''

    # column to use for error bars
    colour_matrix = None
    
    def __init__(self, *args, **kwargs ):
        PlotterMatrix.__init__(self, *args, **kwargs)
        
    def addColourBar( self ):

        axc, kw = matplotlib.colorbar.make_axes(plt.gca())
        cb = matplotlib.colorbar.ColorbarBase(axc, 
                                              cmap=self.color_scheme, 
                                              norm=self.normer )

        
        cb.draw_all()

    def buildMatrices( self, work, **kwargs ):
        '''build matrices necessary for plotting.
        '''
        self.colour_matrix = None

        if self.colour:
            # select label to take
            labels = DataTree.getPaths( work )
            label = list(set(labels[-1]).difference( set((self.colour,)) ))[0]
            self.matrix, self.rows, self.columns = TableMatrix.buildMatrix( self,
                                                                       work, 
                                                                       apply_transformations = True, 
                                                                       take = label,
                                                                       **kwargs 
                                                                       )

            if self.colour and self.colour in labels[-1]:
                self.colour_matrix, rows, colums = TableMatrix.buildMatrix( self,
                                                                       work, 
                                                                       apply_transformations = False, 
                                                                       take = self.colour, 
                                                                       **kwargs
                                                                       )

        else:
            self.matrix, self.rows, self.columns = TableMatrix.buildMatrix( self, work, **kwargs )

        return self.matrix, self.rows, self.columns

    def plotMatrix( self, weight_matrix, 
                    row_headers, col_headers, 
                    vmin, vmax, 
                    color_scheme = None ):
        """
        Temporarily disables matplotlib interactive mode if it is on, 
        otherwise this takes forever.
        """

        def _blob(x,y,area,colour):
            """
            Draws a square-shaped blob with the given area (< 1) at
            the given coordinates.
            """
            hs = numpy.sqrt(area) / 2
            xcorners = numpy.array([x - hs, x + hs, x + hs, x - hs])
            ycorners = numpy.array([y - hs, y - hs, y + hs, y + hs])
            plt.fill(xcorners, ycorners, 
                     edgecolor = colour,
                     facecolor = colour) 

        plt.clf()

        height, width = weight_matrix.shape
        if vmax == None: vmax = weight_matrix.max() # 2**numpy.ceil(numpy.log(numpy.max(numpy.abs(weight_matrix)))/numpy.log(2))
        if vmin == None: vmin = weight_matrix.min()

        scale = vmax - vmin

        if self.colour_matrix != None:
            colour_matrix = self.colour_matrix 
        else:
            colour_matrix = weight_matrix

        cmin, cmax = colour_matrix.min(), colour_matrix.max()
        
        plot = None
        normer = matplotlib.colors.Normalize( cmin, cmax )
        # save for colourbar
        self.normer = normer
        self.color_scheme = color_scheme

        colours = normer( colour_matrix )

        plt.axis('equal')

        for x in range(width):
            for y in range(height):
                _x = x+1
                _y = y+1
                weight = weight_matrix[y,x] - vmin

                _blob(_x - 0.5, 
                      _y - 0.5,
                      weight / scale,
                      color_scheme(colours[y,x]) )

        offset = 0.5
        xfontsize, col_headers = self.mFontSize, col_headers
        yfontsize, row_headers = self.mFontSize, row_headers

        plt.xticks( [ offset + x for x in range(len(col_headers)) ],
                    col_headers,
                    rotation="vertical",
                    fontsize=xfontsize )

        plt.yticks( [ offset + y for y in range(len(row_headers)) ],
                    row_headers,
                    fontsize=yfontsize )

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
                       pos.height * 1.0 / scale_y ))

    # scale figure
    fig.set_figwidth( fig.get_figwidth() * scale_x )
    fig.set_figheight( fig.get_figheight() * scale_y )

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

    Copied originally from http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg04256.html
    but modified.

    There were problems with the automatic re-scaling of the plot. Basically, the legend
    size seemed to be unknown and set to 0,0,1,1. Only after plotting were the correct
    bbox coordinates entered.

    The current implementation allocates 3/4 of the canvas for the legend and
    hopes for the best.
    """

    # make a legend without the location
    # remove the location setting from the kwargs
    if 'loc' in kwargs: loc = kwargs.pop('loc')
    else: loc == "outer-top"

    if loc.endswith( "right" ):
        leg = plt.legend(loc=(1.05,0), *args, **kwargs)
    elif loc.endswith( "top" ):
        leg = plt.legend(loc=(0,1.05), *args, **kwargs)
    else:
        raise ValueError("unknown legend location %s" % loc )

    fig = plt.gcf()
    cid = fig.canvas.mpl_connect('draw_event', on_draw)
    return leg

# the following has been taken from http://www.scipy.org/Cookbook/Matplotlib/HintonDiagrams
def hinton(W, maxWeight=None):
    """
    Draws a Hinton diagram for visualizing a weight matrix. 
    Temporarily disables matplotlib interactive mode if it is on, 
    otherwise this takes forever.
    """
    def _blob(x,y,area,colour):
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
        maxWeight = 2**numpy.ceil(numpy.log(numpy.max(numpy.abs(W)))/numpy.log(2))

    plot = plt.fill(numpy.array([0,width,width,0]),numpy.array([0,0,height,height]),'gray')

    plt.axis('off')
    plt.axis('equal')
    for x in range(width):
        for y in range(height):
            _x = x+1
            _y = y+1
            w = W[y,x]
            if w > 0:
                _blob(_x - 0.5, height - _y + 0.5, min(1,w/maxWeight),'white')
            elif w < 0:
                _blob(_x - 0.5, height - _y + 0.5, min(1,-w/maxWeight),'black')

    if reenable: plt.ion()

    return plot

class LinePlot( Renderer, Plotter ):
    '''create a line plot.

    This :class:`Renderer` requires at least three levels with

    line / label / coords

    This is a base class that provides several hooks for
    derived classes.

    initPlot()

    for line, data in work:
        initLine()

        for label, coords in data:
            xlabel, ylabels = initCoords()
            for ylabel in ylabels:
                addData( xlabel, ylabel )
            finishCoords()
        finishLine()

    finishPlot()

    This plotter accepts the following options:

       :term:`as-lines`: do not plot symbols
    '''
    nlevels = 2

    # do not plot more than five tracks in one plot
    split_at = 5

    options = Plotter.options +\
        ( ('as-lines', directives.flag),
          )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.mAsLines = "as-lines" in kwargs

        if self.mAsLines:
            self.mSymbols = []
            for y in ("-",":","--"):
                for x in "gbrcmyk":
                    self.mSymbols.append( y+x )

    def initPlot(self, fig, work, path ): 

        '''initialize plot.'''
 
        self.legend = []
        self.plots = []
        self.xlabels = []
        self.ylabels = []

    def addData( self, 
                 line, label,
                 xlabel, ylabel,
                 xvals, yvals, 
                 nplotted ):

        s = self.mSymbols[nplotted % len(self.mSymbols)]
        
        xxvals, yyvals = Stats.filterNone( (xvals, yvals) )
        
        self.plots.append( plt.plot( xxvals,
                                     yyvals,
                                     s ) )
        
        self.ylabels.append(ylabel)
        self.xlabels.append(xlabel)

    def initLine( self, line, data ):
        '''hook for code working on a line.'''
        pass

    def initCoords( self, label, coords ):
        '''hook for code working a collection of coords.

        should return a single key for xvalues and 
        one or more keys for y-values.
        '''
        keys = list(coords.keys())
        return keys[0], keys[1:]

    def finishLine( self, line, data ):
        '''hook called after all lines have been processed.'''
        pass

    def finishCoords( self, label, coords ):
        '''hook called after all coords have been processed.'''
        pass

    def finishPlot( self, fig, work, path ):
        '''hook called after plotting has finished.'''
        plt.xlabel( "-".join( set(self.xlabels) ) )
        plt.ylabel( "-".join( set(self.ylabels) ) )
        
    def render(self, work, path ):
        
        fig = self.startPlot()

        # add a default line if there are no lines
        labels = DataTree.getPaths( work )
        if len(labels) == 2: work = odict( (("", work),) )

        self.initPlot( fig, work, path )

        nplotted = 0

        for line, data in work.items():
            
            self.initLine( line, data )

            for label, coords in data.items():

                # sanity check on data
                try: keys = list(coords.keys())
                except AttributeError:
                    self.warn("could not plot %s - coords is not a dict: %s" % (label, str(coords) ))
                    continue
                
                if len(keys) <= 1:
                    self.warn("could not plot %s: not enough columns: %s" % (label, str(coords) ))
                    continue

                xlabel, ylabels = self.initCoords( label, coords)
                xvals = coords[xlabel]

                for ylabel in ylabels:
                    yvals = coords[ylabel]
                    self.addData( line, label, xlabel, ylabel, xvals, yvals, nplotted )
                    nplotted += 1

                    if len(ylabels) > 1:
                        self.legend.append( "/".join((list(map(str, (line,label,ylabel))))))
                    else:
                        self.legend.append( "/".join((list(map(str, (line,label))) )))
                                
                self.xlabels.append(xlabel)

                self.finishCoords( label, coords)

            self.finishLine( line, data )
            
        self.finishPlot( fig, work, path )

        return self.endPlot( self.plots, self.legend, path )
        
class HistogramPlot(LinePlot):        
    '''create a line plot.

    This :class:`Renderer` requires at least three levels:

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
        ( ('error', directives.unchanged),)

    def __init__(self, *args, **kwargs):
        LinePlot.__init__(self,*args, **kwargs)

        try: self.error = kwargs["error"]
        except KeyError: pass

    def initPlot( self, fig, work, path ):
        LinePlot.initPlot( self, fig, work, path )
        self.alpha = 1.0 / len(work)        
        
    def initCoords( self, label, coords ):
        '''collect error coords and compute bar width.'''

        # get and transform x/y values
        keys = list(coords.keys()) 

        xlabel, ylabels = keys[0], keys[1:]

        # locate error bars
        if self.error and self.error in coords:
            self.yerr = coords[self.error]
            ylabels = [ x for x in ylabels if x == self.error ]
        else:
            self.yerr = None
        
        xvals = coords[xlabel]  

        # compute bar widths
        widths = []
        w = xvals[0]
        for x in xvals[1:]:
            widths.append( x-w )
            w=x
        widths.append( widths[-1] )
        self.widths = widths

        self.xvals = xvals

        return xlabel, ylabels

    def addData( self, 
                 line, 
                 label,
                 xlabel, 
                 ylabel,
                 xvals, 
                 yvals, 
                 nplotted ):
        
        self.plots.append( plt.bar( xvals,
                                    yvals,
                                    width = self.widths,
                                    alpha = self.alpha,
                                    yerr = self.yerr,
                                    color = self.mColors[ nplotted % len(self.mColors) ], ) )

    def finishPlot( self, fig, work, path ):

        LinePlot.finishPlot(self, fig, work, path)
        # there is a problem with legends
        # even though len(plts) == len(legend)
        # matplotlib thinks there are more. 
        # In fact, it thinks it is len(plts) = len(legend) * len(xvals)
        self.legend = None
                        
class HistogramGradientPlot(LinePlot):        
    '''create a series of coloured bars from histogram data.

    This :class:`Renderer` requires at least three levels:

    line / data / coords.
    '''
    nlevels = 2

    options = LinePlot.options +\
        ( ('palette', directives.unchanged),
          ('reverse-palette', directives.flag),
          ('colorbar-format', directives.unchanged) )

    def __init__(self, *args, **kwargs):
        LinePlot.__init__(self, *args, **kwargs )

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "Blues"

        self.mReversePalette = "reverse-palette" in kwargs

        if self.mPalette:
            if self.mReversePalette:
                self.color_scheme = plt.get_cmap( "%s_r" % self.mPalette )
            else:
                self.color_scheme = plt.get_cmap( "%s" % self.mPalette )
        else:
            self.color_scheme = None

    def initPlot(self, fig, work, path ):

        LinePlot.initPlot( self, fig, work, path )

        # get min/max x and number of rows
        xmin, xmax = None, None
        ymin, ymax = None, None
        nrows = 0
        self.xvals = None
        for line, data in work.items():

            for label, coords in data.items():

                try: keys = list(coords.keys())
                except AttributeError: continue
                if len(keys) <= 1: continue
                
                xvals = coords[keys[0]]
                if self.xvals == None:
                    self.xvals = xvals
                elif not numpy.all(self.xvals == xvals):
                    raise ValueError("Gradient-Histogram-Plot requires the same x values.")

                if xmin == None: 
                    xmin, xmax = min(xvals), max(xvals)
                else:
                    xmin = min(xmin, min(xvals))
                    xmax = max(xmax, max(xvals))

                for ylabel in keys[1:]:
                    yvals = coords[ylabel]
                    if ymin == None: 
                        ymin, ymax = min(yvals), max(yvals)
                    else:
                        ymin = min(ymin, min(yvals))
                        ymax = max(ymax, max(yvals))

                nrows += len(keys)-1
                
        self.nrows = nrows
        self.ymin, self.ymax = ymin, ymax

        if self.zrange:
            self.ymin, self.ymax = self.zrange

    def addData( self, line, label, xlabel, ylabel,
                 xvals, yvals, nplotted ):

        if self.zrange:
            vmin, vmax = self.zrange
            if vmin == None: vmin = yvals.min()
            if vmax == None: vmax = yvals.max()
            yvals[ yvals < vmin ] = vmin
            yvals[ yvals > vmax ] = vmax

        a = numpy.vstack((yvals,yvals))

        ax = plt.subplot(self.nrows, 1, nplotted+1)
        self.plots.append( plt.imshow(a,
                                      aspect='auto', 
                                      cmap=self.color_scheme, 
                                      origin='lower',
                                      vmax = self.ymax,
                                      vmin = self.ymin ) )

        # add legend on left-hand side
        pos = list(ax.get_position().bounds)
        self.mCurrentFigure.text(pos[0] - 0.01, 
                                 pos[1], 
                                 line,
                                 horizontalalignment='right')

        ax = plt.gca()
        plt.setp(ax.get_xticklabels(), visible=False)
        plt.setp(ax.get_yticklabels(), visible=False)

    def finishPlot( self, fig, work, path ):

        ax = plt.gca() 
        plt.setp(ax.get_xticklabels(), visible=True)
        increment = len(self.xvals ) // 5
        ax.set_xticks( range( 0, len(self.xvals), increment ) ) 
        ax.set_xticklabels( [self.xvals[x] for x in range( 0, len(self.xvals), increment ) ] )

        LinePlot.finishPlot(self, fig, work, path)
        self.legend = None

        # add colorbar on the right
        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
        cax = plt.axes([0.85, 0.1, 0.075, 0.8])
        plt.colorbar(cax=cax, format=self.mBarFormat )

class BarPlot( TableMatrix, Plotter):
    '''A bar plot.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    '''

    options = TableMatrix.options + Plotter.options +\
        ( ('label', directives.unchanged),
          ('error', directives.unchanged), 
          ('colour', directives.unchanged),
          ('transparency', directives.unchanged),
          ('bottom-value', directives.unchanged),
          ('orientation', directives.unchanged),
          ('first-is-offset', directives.unchanged),
          ('switch', directives.unchanged ),
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

    # bottom value of bars (can be used to move intersection of x-axis with y-axis)
    bottom_value = None

    label_offset_x = 10
    label_offset_y = 5

    # orientation of bars
    orientation = 'vertical'

    # first row is offset (not plotted)
    first_is_offset = False

    # switch rows/columns
    switch_row_col = False

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.error = kwargs.get("error", None )
        self.label = kwargs.get("label", None )
        self.colour = kwargs.get("colour", None )
        self.switch_row_col = 'switch' in kwargs
        self.transparency = kwargs.get("transparency", None )
        if self.transparency: raise NotImplementedError( "transparency not implemented yet")
        self.orientation = kwargs.get( 'orientation', 'vertical' )

        if self.orientation == 'vertical':
            self.plotf = plt.bar
        else:
            self.plotf = plt.barh

        if self.error or self.label:
            self.nlevels += 1

        self.bottom_value = kwargs.get("bottom-value", None )
        self.first_is_offset = 'first-is-offset' in kwargs

        self.bar_patterns = list(itertools.product( self.mPatterns, self.mColors) )

    def addLabels( self, xvals, yvals, labels ):
        '''add labels at x,y at current plot.
        '''

        def coord_offset(ax, fig, x, y):
            return matplotlib.transforms.offset_copy(ax.transData, fig, x=x, y=y, units='dots')

        if self.orientation == 'horizontal':
            xvals,yvals=yvals,xvals

        ax = plt.gca()
        trans=coord_offset(ax, self.mCurrentFigure, 
                           self.label_offset_x, 
                           self.label_offset_y)
        for xval, yval, label in zip(xvals,yvals,labels):
            ax.text(xval, yval, label, transform=trans)

    def buildMatrices( self, work ):
        '''build matrices necessary for plotting.
        '''

        self.error_matrix = None
        self.label_matrix = None
        self.colour_matrix = None
        self.transparency_matrix = None

        if self.error or self.label or self.colour or self.transparency:
            labels = DataTree.getPaths( work )
            ignore = set()
            if self.error and self.error in labels[-1]:
                self.error_matrix, rows, colums = self.buildMatrix( work, 
                                                                    apply_transformations = False, 
                                                                    take = self.error
                                                                    )
                ignore.add( self.error )

            if self.label and self.label in labels[-1]:
                self.label_matrix, rows, colums = self.buildMatrix( work, 
                                                                    apply_transformations = False, 
                                                                    missing_value = "",
                                                                    take = self.label,
                                                                    dtype = "S20",
                                                                    )
                ignore.add( self.label )

            if self.colour and self.colour in labels[-1]:
                self.colour_matrix, rows, colums = self.buildMatrix( work, 
                                                                     apply_transformations = False, 
                                                                     missing_value = "",
                                                                     take = self.colour,
                                                                     dtype = "S20",
                                                                     )
                ignore.add( self.colour)
                

            if self.transparency and self.transparency in labels[-1]:
                self.transparency_matrix, rows, colums = self.buildMatrix( work, 
                                                                           apply_transformations = False, 
                                                                           missing_value = 1.0,
                                                                           take = self.transparency,
                                                                           dtype = numpy.float,
                                                                     )
                ignore.add( self.transparency)

            # select label to take, preserve order
            self.matrix, self.rows, self.columns = self.buildMatrix( work, 
                                                                     apply_transformations = True, 
                                                                     ignore = ignore,
                                                                     )
                
        else:
            self.matrix, self.rows, self.columns = self.buildMatrix( work )

        if self.switch_row_col:
            if self.matrix != None: self.matrix = self.matrix.transpose()
            if self.error_matrix != None: self.error_matrix = self.error_matrix.transpose()
            if self.label_matrix != None: self.label_matrix = self.label_matrix.transpose()
            if self.colour_matrix != None: self.colour_matrix = self.colour_matrix.transpose()
            if self.transparency_matrix != None: self.transparency_matrix = self.transparency_matrix.transpose()
            self.rows, self.columns = self.columns, self.rows

    def getColour( self, idx, column ):
        '''return hatch and colour.'''
        
        if self.transparency_matrix != None:
            alpha = self.transparency_matrix[:,column]
        else:
            alpha = None
        
        if self.colour_matrix != None:
            color = self.colour_matrix[:,column]
            hatch = None
        else:
            hatch, color = self.bar_patterns[ idx % len(self.bar_patterns) ]
        return hatch, color, alpha
            
    def render( self, work, path ):

        self.buildMatrices( work )
        plts = []

        self.startPlot()

        xvals = numpy.arange( 0, len(self.rows) )

        # plot by row
        y, error = 0, None
        for column,header in enumerate(self.columns):
            
            vals = self.matrix[:,column]
            if self.error: error = self.error_matrix[:,column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if numpy.isnan(vals[0]) or numpy.isinf( vals[0] ): 
                vals[0] = 0
                
            hatch, color, alpha = self.getColour( y, column )

            
            if self.bottom_value != None:
                bottom = float(self.bottom_value)
            else:
                bottom = None
             
            plts.append( self.plotf( xvals, 
                                     vals,
                                     self.width, 
                                     yerr = error,
                                     ecolor = "black",
                                     color = color,
                                     hatch = hatch,
                                     alpha = alpha,
                                     )[0] )
                

            if self.label and self.label_matrix != None: 
                self.addLabels( xvals, vals, self.label_matrix[:,column] )
            
            y += 1

            
        rotation = "horizontal"
        
        if self.orientation == "vertical":
            if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
                rotation = "vertical"
                self.rescaleForVerticalLabels( self.rows )
        
        if self.orientation == 'vertical':
            plt.xticks( xvals + 0.5, self.rows, rotation = rotation )
        else:
            plt.yticks( xvals + 0.5, self.rows, rotation = rotation )

        return self.endPlot( plts, self.columns, path )

class InterleavedBarPlot(BarPlot):
    """A plot with interleaved bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    def __init__(self, *args, **kwargs):
        BarPlot.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        self.buildMatrices( work )

        self.startPlot()

        width = 1.0 / (len(self.columns) + 1 )
        plts, error = [], None
        xvals = numpy.arange( 0, len(self.rows) )
        offset = width / 2.0

        # plot by row
        row = 0

        for column,header in enumerate(self.columns):
            
            vals = self.matrix[:,column]
            if self.error: error = self.error_matrix[:,column]
            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if numpy.isnan(vals[0]) or numpy.isinf( vals[0] ): 
                vals[0] = 0

            hatch, color, alpha = self.getColour( row, column )
            
            if self.bottom_value != None:
                bottom = float(self.bottom_value)
            else:
                bottom = None

            kwargs = {}
            if self.orientation == 'vertical': kwargs['bottom'] = bottom
            else: kwargs['left'] = bottom

            plts.append( self.plotf( xvals + offset, 
                                     vals,
                                     width,
                                     yerr = error,
                                     align = "edge",
                                     ecolor = "black",
                                     color = color,
                                     hatch = hatch,
                                     alpha = alpha,
                                     **kwargs
                                     )[0])
            
            if self.label and self.label_matrix != None: 
                self.addLabels( xvals+offset, vals, self.label_matrix[:,column] )

            offset += width
            row += 1

        rotation = "horizontal"

        if self.orientation == "vertical":
            if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
                rotation = "vertical"
                self.rescaleForVerticalLabels( self.rows )
            else: 
                rotation = "horizontal"
                
        if self.orientation == 'vertical':
            plt.xticks( xvals + 0.5, self.rows, rotation = rotation )
        else:
            plt.yticks( xvals + 0.5, self.rows, rotation = rotation )

        return self.endPlot( plts, self.columns, path )
           
class StackedBarPlot(BarPlot ):
    """A plot with stacked bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """
    def __init__(self, *args, **kwargs):
        BarPlot.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        self.buildMatrices( work)
        
        self.startPlot( )

        plts = []

        xvals = numpy.arange( (1.0 - self.width) / 2., len(self.rows) )
        sums = numpy.zeros( len(self.rows), numpy.float )
        
        y, error, is_first = 0, None, True
        legend = []
        colour_offset = 0

        for column, header in enumerate(self.columns):

            vals = self.matrix[:,column]            
            if self.error: error = self.error_matrix[:,column]
            
            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if numpy.isnan(vals[0]) or numpy.isinf( vals[0] ): 
                vals[0] = 0

            kwargs = {}
            if self.orientation == 'vertical': kwargs['bottom'] = sums
            else: kwargs['left'] = sums

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
            
            hatch, color, alpha = self.getColour( y, column - colour_offset )

            plts.append( self.plotf( xvals, 
                                     vals, 
                                     self.width, 
                                     yerr = error,
                                     color = color,
                                     hatch = hatch,
                                     alpha = alpha,
                                     ecolor = "black",
                                     **kwargs ) [0] )

            if self.label and self.label_matrix != None: 
                self.addLabels( xvals, vals, self.label_matrix[:,column] )
            legend.append( header )
            sums += vals
            y += 1

        rotation = "horizontal"

        if self.orientation == "vertical":
            if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
                rotation = "vertical"
                self.rescaleForVerticalLabels( self.rows )
                
        if self.orientation == 'vertical':
            plt.xticks( xvals + self.width / 2., 
                        self.rows,
                        rotation = rotation )
        else:
            plt.yticks( xvals + self.width / 2., 
                        self.rows,
                        rotation = rotation )
            


        return self.endPlot( plts, legend, path )

class PiePlot(Renderer, Plotter):
    """A pie chart.

    This :class:`Renderer` requires one level:
    entries[dict] 

    If *pie-first-is-total* is set, the first entry
    is assumed to be the total and all the other values
    are subtracted. It is renamed by the value of *pie-first-is-total*.
    """
    options = TableMatrix.options + Plotter.options +\
        (('pie-min-percentage', directives.unchanged),
         ('pie-first-is-total', directives.unchanged), )

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.mPieMinimumPercentage = float( kwargs.get("pie-min-percentage", 0 ))

        self.mFirstIsTotal = kwargs.get( "pie-first-is-total", None )

        # store a list of sorted headers to ensure the same sort order
        # in all plots.
        self.sorted_headers = odict()

    def render( self, work, path ):
        
        self.startPlot()

        for x in list(work.keys()): 
            if x not in self.sorted_headers: 
                self.sorted_headers[x] = len(self.sorted_headers)

        sorted_vals = [0] * len(self.sorted_headers)

        for key, value in work.items():
            if value < self.mPieMinimumPercentage:
                sorted_vals[self.sorted_headers[key]] = 0
                if "other" not in self.sorted_headers:
                    self.sorted_headers["other"] = len(self.sorted_headers)
                    sorted_vals.append( 0 )
                sorted_vals[self.sorted_headers["other"]] += value
            else:
                sorted_vals[self.sorted_headers[key]] = value

        labels = list(self.sorted_headers.keys())

        if sum(sorted_vals) == 0:
            return self.endPlot( None, None, path )

        # subtract others from total - rest
        if self.mFirstIsTotal:
            sorted_vals[0] -= sum(sorted_vals[1:])
            if sorted_vals[0] < 0: raise ValueError( "option first-is-total used, but first < rest" )
            labels[0] = self.mFirstIsTotal

        return self.endPlot( plt.pie( sorted_vals, labels = labels ), None, path )

class TableMatrixPlot(TableMatrix, PlotterMatrix):
    """Render a matrix as a matrix plot.
    """
    options = TableMatrix.options + PlotterMatrix.options

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def render( self, work, path ):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix( work )
        self.debug("building matrix finished")
        return self.plot( matrix, rows, columns, path )

# for compatibility
MatrixPlot = TableMatrixPlot

class NumpyMatrixPlot(NumpyMatrix, PlotterMatrix):
    """Render a matrix as a matrix plot.
    """
    options = NumpyMatrix.options + PlotterMatrix.options

    def __init__(self, *args, **kwargs):
        NumpyMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def render( self, work, path ):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix( work )
        self.debug("building matrix finished")
        return self.plot( matrix, rows, columns, path )

class HintonPlot(TableMatrix, PlotterHinton):
    """Render a matrix as a hinton plot.

    Draws a Hinton diagram for visualizing a weight matrix. 

    The size of a box reflects the weight.

    This class adds the following options to the :term:`report` directive:

       :term:`colours`: colour boxes according to value.

    """
    options = TableMatrix.options + PlotterHinton.options +\
        ( ('colours', directives.unchanged), 
          )

    # column to use for error bars
    colour = None

    def __init__(self, *args, **kwargs):
        TableMatrix.__init__(self, *args, **kwargs )
        PlotterHinton.__init__(self, *args, **kwargs )

        self.colour = kwargs.get("colour", None )

        if self.colour: self.nlevels += 1

    def render( self, work, path ):
        """render the data."""

        matrix, rows, columns = self.buildMatrices( work )

        return self.plot( matrix, rows, columns, path )

class BoxPlot(Renderer, Plotter):        
    """Write a set of box plots.
    
    This :class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    options = Renderer.options + Plotter.options

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render(self, work, path ):

        self.startPlot()

        plts, legend = [], []
        all_data = []

        # for line, data in work.iteritems():

            # assert len(data) == 1, "multicolumn data not supported yet, got %i items" % len(data)

        for label, values in work.items():
            assert Utils.isArray( values ), "work is of type '%s'" % values
            d = [ x for x in values if x != None ]
            if len(d) > 0:
                all_data.append( d )
                legend.append( "/".join( (str(path),str(label))))

        if len(all_data) == 0: 
            return self.endPlot( plts, None, path )
            raise ValueError("no data" )
            
        plts.append( plt.boxplot( all_data ) )
        
        if len( legend ) > 5 or max( [len(x) for x in legend] ) >= 8 : 
            rotation = "vertical"
        else: 
            rotation = "horizontal"

        plt.xticks( [ x + 1 for x in range(0,len(legend)) ],
                    legend,
                    rotation = rotation )

        return self.endPlot( plts, None, path )

class GalleryPlot(Renderer, Plotter):
    '''Plot an image.
    '''

    options = Renderer.options + Plotter.options
    
    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render(self, work, path ):

        if "filename" not in work: 
            self.warn( "no 'filename' key in path %s" % path )
            return


        rst_text = '''.. figure:: %(fn)s
'''

        rst_link = '''* `%(title)s <%(absfn)s>`_ 
'''
        title = path2str( path )
        fn = work["filename"]
        absfn = os.path.abspath( fn ) 
        # do not render svg images
        if fn.endswith(".svg" ):
            title = os.path.basename( fn )
            return ResultBlocks( ResultBlock( text = rst_text % locals(),
                                              title = title ) )
        # do not render pdf images
        elif fn.endswith( ".pdf"):
            title = os.path.basename( fn )
            return ResultBlocks( ResultBlock( text = rst_link % locals(),
                                              title = title ) )
        
        self.startPlot()
        
        plts = []
        try:
            data = plt.imread( fn )
        except IOError:
            raise ValueError( "file format for file '%s' not recognized" % fn )
    
        ax = plt.gca()
        ax.axison = False
        plts.append( plt.imshow( data ) )
        
        return self.endPlot( plts, None, path )
                                     
class ScatterPlot(Renderer, Plotter):
    """Scatter plot.

    The different tracks will be displayed with different colours.

    This :class:`Renderer` requires two levels:
    track[dict] / coords[dict]

    :regression:
       int

       add linear regression function of a certain degree
       (straight line is degree 1).

    """
    options = Renderer.options + Plotter.options +\
        ( ('regression', directives.unchanged), 
          )
    
    nlevels = 2

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        # plt.scatter does not permitting setting
        # options in rcParams - hence the parameters
        # are parsed explicitely here

        self.markersize = self.mMPLRC.get( "lines.markersize", 
                                           plt.rcParams.get( "lines.markersize", 6 ) )

        self.markeredgewidth = self.mMPLRC.get( "lines.markeredgewith", 
                                                plt.rcParams.get("lines.markeredgewidth",
                                                                 0.5 ) )
        
        self.regression = int(kwargs.get( "regression", 0 ))
        
    def render(self, work, path ):
        
        self.startPlot()
        
        nplotted = 0

        plts, legend = [], []
        xlabels, ylabels = [], []

        for label, coords in work.items():
            assert len(coords) >= 2, "expected at least two arrays, got %i" % len(coords)
            
            k = list(coords.keys())
            
            xlabel = k[0]

            for ylabel in k[1:]:
                xvals, yvals = Stats.filterNone( (coords[xlabel],
                                                  coords[ylabel]) )

                marker = self.mMarkers[nplotted % len(self.mMarkers)]
                color = self.mColors[nplotted % len(self.mColors)]
                if len(xvals) == 0 or len(yvals) == 0: continue

                # plt.scatter does not permitting setting
                # options in rcParams, so all is explict
                plts.append(plt.scatter( xvals,
                                         yvals,
                                         marker = marker,
                                         c = color,
                                         linewidths = self.markeredgewidth,
                                         s = self.markersize) )
                legend.append( label )
                
                if self.regression:
                    coeffs = numpy.polyfit(xvals, yvals, self.regression)
                    p = numpy.poly1d(coeffs)
                    svals = sorted( xvals )
                    plts.append( plt.plot( svals, 
                                           [ p(x) for x in svals ],
                                           c = color,
                                           marker = 'None') )
                    
                    legend.append( "regression %s" % label )

                nplotted += 1

                xlabels.append( xlabel )
                ylabels.append( ylabel )
            
        plt.xlabel( ":".join( set(xlabels) ) )
        plt.ylabel( ":".join( set(ylabels) ) )
        
        return self.endPlot( plts, legend, path )

class ScatterPlotWithColor( ScatterPlot ):
    """Scatter plot with individual colors for each dot.

    This class adds the following options to the :term:`report` directive:

       :term:`colorbar-format`: numerical format for the colorbar.

       :term:`palette`: numerical format for the colorbar.

       :term:`zrange`: restrict plot a part of the z-axis.

    This :class:`Renderer` requires one level:

    coords[dict]
    """
    options = Renderer.options + Plotter.options +\
        ( ('palette', directives.unchanged),
          ('reverse-palette', directives.flag),
          ('colorbar-format', directives.unchanged) )

    nlevels = 1

    def __init__(self, *args, **kwargs):
        ScatterPlot.__init__(self, *args, **kwargs )

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        self.mReversePalette = "reverse-palette" in kwargs

    def render(self, work, path):

        self.startPlot()
        
        plts = []

        if self.mPalette:
            if self.mReversePalette:
                color_scheme = eval( "plt.cm.%s_r" % self.mPalette)                    
            else:
                color_scheme = eval( "plt.cm.%s" % self.mPalette)
        else:
            color_scheme = None

        assert len(work) >= 3, "expected at least three arrays, got %i: %s" % (len(work), list(work.keys()))
        
        xlabel, ylabel, zlabel = list(work.keys())[:3]
        xvals, yvals, zvals = Stats.filterNone( list(work.values())[:3])

        if len(xvals) == 0 or len(yvals) == 0 or len(zvals) == 0: 
            raise ValueError("no data" )

        if self.zrange:
            vmin, vmax = self.zrange
            zvals = numpy.array( zvals )
            zvals[ zvals < vmin ] = vmin
            zvals[ zvals > vmax ] = vmax
        else:
            vmin, vmax = None, None

        # plt.scatter does not permitting setting
        # options in rcParams, so all is explict
        plts.append(plt.scatter( xvals,
                                 yvals,
                                 s = self.markersize,
                                 c = zvals,
                                 linewidths = self.markeredgewidth,
                                 cmap = color_scheme,
                                 vmax = vmax,
                                 vmin = vmin ) )
            
        plt.xlabel( xlabel )
        plt.ylabel( ylabel )

        cb = plt.colorbar( format = self.mBarFormat)        
        cb.ax.set_xlabel( zlabel )

        return self.endPlot( plts, None, path )


class VennPlot( Renderer, Plotter ):
    '''plot a two and three circle venn diagramm.

    This :term:`renderer` plots a Venn diagramm.

    This :class:`Renderer` requires two levels.

    The data dictionary requires two entries, a
    list of set labels and a dictionary of
    set sizes.

    The dictionary should contain the elements
    * ('10', '01', and '11') for a two-circle Venn diagram.
    * ('100', '010', '110', '001', '101', '011', '111') for a three-circle Venn diagram.

    When plotting, the function looks for the first 3 or 7 element dictionary
    and the first 3 or 7 element list.

    data[dict]
    '''

    options = Renderer.options + Plotter.options

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def __call__(self, work, path):

        if matplotlib_venn == None:
            raise ValueError("library matplotlib_venn not available")

        self.startPlot()

        plts = []

        subsets = dict( work )
        if "labels" in subsets:
            setlabels = subsets["labels"]
            del subsets["labels"]

        if subsets == None:
            self.warn( "no suitable data for Venn diagram at %s" % path)
            return self.endPlot( plts, None, path )

        if len(subsets) == 3:
            if setlabels:
                if len(setlabels) != 2: raise ValueError( "require two labels, got %i" % len(setlabels))
            plts.append( matplotlib_venn.venn2( subsets,
                                                set_labels = setlabels ) )
        elif len(subsets) == 7:
            if setlabels:
                if len(setlabels) != 3: raise ValueError( "require three labels, got %i" % len(setlabels))
            plts.append( matplotlib_venn.venn3( subsets,
                                                set_labels = setlabels ) )
        else:
            raise ValueError( "require 3 or 7 values for a Venn diagramm, got %i" % len(subset))    

        return self.endPlot( plts, None, path )
