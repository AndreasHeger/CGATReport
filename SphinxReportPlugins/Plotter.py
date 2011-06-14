"""Mixin classes for Renderers that plot.
"""

import os, sys, re, math

import matplotlib
matplotlib.use('Agg', warn = False)
# This does not work:
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own matplotlibrc.

import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReportPlugins.Renderer import Renderer, Matrix
from SphinxReport.odict import OrderedDict as odict
from SphinxReport import Utils, DataTree, Stats

from docutils.parsers.rst import directives

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

       :term:`as-lines`: do not plot symbols

       :term:`xrange`: restrict plot a part of the x-axis

       :term:`yrange`: restrict plot a part of the y-axis

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
        ('mpl-figure',  directives.unchanged),
        ('mpl-legend',  directives.unchanged),
        ('mpl-subplot',  directives.unchanged),
        ('mpl-rc',  directives.unchanged), 
        ('as-lines', directives.flag),
        ('legend-location',  directives.unchanged),
        )

    def __init__(self, *args, **kwargs ):
        """parse option arguments."""

        self.mFigure = 0
        self.mColors = "bgrcmk"
        self.mSymbols = ["g-D","b-h","r-+","c-+","m-+","y-+","k-o","g-^","b-<","r->","c-D","m-h"]
        self.mMarkers = "so^>dph8+x"

        self.logscale = kwargs.get("logscale", None )
        self.title = kwargs.get("title", None )
        self.add_title = "add-title" in kwargs
        self.xlabel = kwargs.get("xtitle", None )
        self.ylabel = kwargs.get("ytitle", None )

        # substitute '-' in SphinxReport-speak for ' ' in matplotlib speak
        self.legend_location = re.sub("-", " ", kwargs.get("legend-location", "outer-top"))

        self.width = kwargs.get("width", 0.50 )
        self.mAsLines = "as-lines" in kwargs
        self.xrange = parseRanges(kwargs.get("xrange", None ))
        self.yrange = parseRanges(kwargs.get("yrange", None ))
        self.zrange = parseRanges(kwargs.get("zrange", None ))

        if self.mAsLines:
            self.mSymbols = []
            for y in ("-",":","--"):
                for x in "gbrcmyk":
                    self.mSymbols.append( y+x )

 
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
        """close a plot.

        Returns blocks of restructured text with place holders for the current 
        figure(s).
        """

        # set logscale before the xlim, as it re-scales the plot.
        if self.logscale:
            ax = plt.gca()
            if "x" in self.logscale:
                try:
                    ax.set_xscale('log')
                except OverflowError:
                    ax.set_xscale('linear')

            if "y" in self.logscale:
                try:
                    ax.set_yscale('log')
                except OverflowError:
                    ax.set_yscale('linear')
                
            ax.relim()

        if self.xrange:
            plt.xlim( self.xrange )
        if self.yrange:
            plt.ylim( self.yrange )
            
        if self.add_title: plt.suptitle( "/".join(path) )

        blocks = ResultBlocks( ResultBlock( "\n".join( ("#$mpl %i$#" % (self.mFigure), "")), title = "/".join(path) ) )

        legend = None
        maxlen = 0

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

       :term:`zrange`: restrict plot a part of the z-axis.

    """

    mFontSize = 8

    # after # characters, split into two
    # lines
    mSplitHeader = 20
    mFontSizeSplit = 8

    # separators to use to split text
    mSeparators = " :_"

    options = Plotter.options +\
        ( ('palette', directives.unchanged),
          ('reverse-palette', directives.flag),
          ('max-rows', directives.unchanged),
          ('max-cols', directives.unchanged),
          ('colorbar-format', directives.unchanged) )

    def __init__(self, *args, **kwargs ):
        Plotter.__init__(self, *args, **kwargs)

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        try: self.mMaxRows = kwargs["max-rows"]
        except KeyError: self.mMaxRows = 20

        try: self.mMaxCols = kwargs["max-cols"]
        except KeyError: self.mMaxCols = 20

        self.mReversePalette = "reverse-palette" in kwargs

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

        plot = plt.imshow(matrix,
                          cmap=color_scheme,
                          origin='lower',
                          vmax = vmax,
                          vmin = vmin,
                          interpolation='nearest')

        # offset=0: x=center,y=center
        # offset=0.5: y=top/x=right
        offset = 0.0

        col_headers = [ str(x) for x in col_headers ]
        row_headers = [ str(x) for x in row_headers ]
        
        # determine fontsize for labels
        xfontsize, col_headers = self.mFontSize, col_headers
        yfontsize, row_headers = self.mFontSize, row_headers

        plt.xticks( [ offset + x for x in range(len(col_headers)) ],
                    col_headers,
                    rotation="vertical",
                    fontsize=xfontsize )

        plt.yticks( [ offset + y for y in range(len(row_headers)) ],
                    row_headers,
                    fontsize=yfontsize )

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
            if self.mReversePalette:
                color_scheme = eval( "plt.cm.%s_r" % self.mPalette)                    
            else:
                color_scheme = eval( "plt.cm.%s" % self.mPalette)
        else:
            color_scheme = None

        plots = []

        split_row, split_col = nrows > self.mMaxRows, ncols > self.mMaxCols

        if (split_row and split_col) or not (split_row or split_col):
            self.debug("not splitting matrix")
            # do not split small or symmetric matrices
            cax = self.plotMatrix( matrix, row_headers, col_headers, vmin, vmax, color_scheme )
            plots, labels = None, None
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
                self.plotMatrix( matrix[start:end,:], 
                                 new_headers[start:end], 
                                 col_headers, 
                                 vmin, vmax,
                                 color_scheme )
            labels = ["%s: %s" % x for x in zip( new_headers, row_headers) ]
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
                self.plotMatrix( matrix[:,start:end], 
                                 row_headers, 
                                 new_headers[start:end], 
                                 vmin, vmax,
                                 color_scheme ) 
            labels = ["%s: %s" % x for x in zip( new_headers, col_headers) ]
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
            self.matrix, self.rows, self.columns = Matrix.buildMatrix( self,
                                                                       work, 
                                                                       apply_transformations = True, 
                                                                       take = label,
                                                                       **kwargs 
                                                                       )

            if self.colour and self.colour in labels[-1]:
                self.colour_matrix, rows, colums = Matrix.buildMatrix( self,
                                                                       work, 
                                                                       apply_transformations = False, 
                                                                       take = self.colour, 
                                                                       **kwargs
                                                                       )

        else:
            self.matrix, self.rows, self.columns = Matrix.buildMatrix( self, work, **kwargs )

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
            hs = np.sqrt(area) / 2
            xcorners = np.array([x - hs, x + hs, x + hs, x - hs])
            ycorners = np.array([y - hs, y - hs, y + hs, y + hs])
            plt.fill(xcorners, ycorners, 
                     edgecolor = colour,
                     facecolor = colour) 

        plt.clf()

        height, width = weight_matrix.shape
        if vmax == None: vmax = weight_matrix.max() # 2**np.ceil(np.log(np.max(np.abs(weight_matrix)))/np.log(2))
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

        for x in xrange(width):
            for y in xrange(height):
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
        hs = np.sqrt(area) / 2
        xcorners = np.array([x - hs, x + hs, x + hs, x - hs])
        ycorners = np.array([y - hs, y - hs, y + hs, y + hs])
        plt.fill(xcorners, ycorners, colour, edgecolor=colour)

    reenable = False
    if plt.isinteractive(): 
        reenable = True
        plt.ioff()

    plt.clf()

    height, width = W.shape
    if not maxWeight:
        maxWeight = 2**np.ceil(np.log(np.max(np.abs(W)))/np.log(2))

    plot = plt.fill(np.array([0,width,width,0]),np.array([0,0,height,height]),'gray')

    plt.axis('off')
    plt.axis('equal')
    for x in xrange(width):
        for y in xrange(height):
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

    This :class:`Renderer` requires at least three levels:

    line / data / coords.

    This is a base class that provides several hooks for
    derived classes.

    initPlot()

    for line, data in work:
        initLine()

        for coords in data:
            xlabel, ylabels = initCoords()
            for ylabel in ylabels:
                addData( xlabel, ylabel )
            finishCoords()
        finishLine()

    finishPlot()
    '''
    nlevels = 3

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

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
        
        self.plots.append( plt.plot( xvals,
                                     yvals,
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
        keys = coords.keys()
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

        self.initPlot( fig, work, path )

        nplotted = 0

        for line, data in work.iteritems():
            
            self.initLine( line, data )

            for label, coords in data.iteritems():

                # sanity check on data
                try: keys = coords.keys()
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
                        self.legend.append( "/".join((line,label,ylabel) ))
                    else:
                        self.legend.append( "/".join((line,label) ))
                                
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
    nlevels = 3

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
        keys = coords.keys() 

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
    nlevels = 3

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
        for line, data in work.iteritems():

            for label, coords in data.iteritems():

                try: keys = coords.keys()
                except AttributeError: continue
                if len(keys) <= 1: continue
                
                xvals = coords[keys[0]]
                if self.xvals == None:
                    self.xvals = xvals
                elif not np.all(self.xvals == xvals):
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

        a = np.vstack((yvals,yvals))

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
        ax.set_xticks( xrange( 0, len(self.xvals), increment ) ) 
        ax.set_xticklabels( [self.xvals[x] for x in xrange( 0, len(self.xvals), increment ) ] )

        LinePlot.finishPlot(self, fig, work, path)
        self.legend = None

        # add colorbar on the right
        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
        cax = plt.axes([0.85, 0.1, 0.075, 0.8])
        plt.colorbar(cax=cax, format=self.mBarFormat )

class BarPlot( Matrix, Plotter):
    '''A bar plot.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    '''

    options = Matrix.options + Plotter.options +\
        ( ('label', directives.unchanged),
          ('error', directives.unchanged), )
        
    # column to use for error bars
    error = None

    # column to use for labels
    label = None

    label_offset_x = 10
    label_offset_y = 5

    def __init__(self, *args, **kwargs):
        Matrix.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.error = kwargs.get("error", None )
        self.label = kwargs.get("label", None )

        if self.error or self.label:
            self.nlevels += 1
 
    def addLabels( self, xvals, yvals, labels ):
        '''add labels at x,y at current plot.'''

        def coord_offset(ax, fig, x, y):
            return matplotlib.transforms.offset_copy(ax.transData, fig, x=x, y=y, units='dots')

            ax = plt.gca()
            trans=coord_offset(ax, self.mCurrentFigure, self.label_offset_x, self.label_offset_y)
            for xval, yval, label in zip(xvals,vals,labels):
                ax.text(xval, yval, label, transform=trans)

    def buildMatrices( self, work ):
        '''build matrices necessary for plotting.
        '''
        self.error_matrix = None
        self.label_matrix = None
        
        if self.error or self.label:
            # select label to take
            labels = DataTree.getPaths( work )
            label = list(set(labels[-1]).difference( set((self.error, self.label)) ))[0]
            self.matrix, self.rows, self.columns = self.buildMatrix( work, 
                                                                     apply_transformations = True, 
                                                                     take = label
                                                                     )
            if self.error and self.error in labels[-1]:
                self.error_matrix, rows, colums = self.buildMatrix( work, 
                                                                    apply_transformations = False, 
                                                                    take = self.error
                                                                    )
            if self.label and self.label in labels[-1]:
                self.label_matrix, rows, colums = self.buildMatrix( work, 
                                                                    apply_transformations = False, 
                                                                    missing_value = "",
                                                                    take = self.label,
                                                                    dtype = "S20",
                                                                    )

        else:
            self.matrix, self.rows, self.columns = self.buildMatrix( work )

    def render( self, work, path ):

        self.buildMatrices( work )
        plts = []

        self.startPlot()

        xvals = np.arange( 0, len(self.rows) )

        # plot by row
        y, error = 0, None
        for column,header in enumerate(self.columns):
            
            vals = self.matrix[:,column]
            if self.error: error = self.error_matrix[:,column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if np.isnan(vals[0]) or np.isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals, 
                                  vals,
                                  self.width, 
                                  yerr = error,
                                  ecolor = "black",
                                  color = self.mColors[ y % len(self.mColors) ],
                                  )[0] )

            if self.label and self.label_matrix != None: 
                self.addLabels( xvals, vals, self.label_matrix[:,column] )
            
            y += 1

        if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( self.rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + 0.5, self.rows, rotation = rotation )

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
        xvals = np.arange( 0, len(self.rows) )
        offset = width / 2.0

        # plot by row
        row = 0

        for column,header in enumerate(self.columns):
            
            vals = self.matrix[:,column]
            if self.error: error = self.error_matrix[:,column]
            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if np.isnan(vals[0]) or np.isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals + offset, 
                                  vals,
                                  width,
                                  yerr = error,
                                  align = "edge",
                                  ecolor = "black",
                                  color = self.mColors[ row % len(self.mColors) ],
                                  )[0])
            
            if self.label and self.label_matrix != None: 
                self.addLabels( xvals+offset, vals, self.label_matrix[:,column] )

            offset += width
            row += 1

        if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( self.rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + 0.5, self.rows, rotation = rotation )

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

        xvals = np.arange( (1.0 - self.width) / 2., len(self.rows) )
        sums = np.zeros( len(self.rows), np.float )

        y, error = 0, None
        for column,header in enumerate(self.columns):

            vals = self.matrix[:,column]            
            if self.error: error = self.error_matrix[:,column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if np.isnan(vals[0]) or np.isinf( vals[0] ): 
                vals[0] = 0
                
            plts.append( plt.bar( xvals, 
                                  vals, 
                                  self.width, 
                                  yerr = error,
                                  color = self.mColors[ y % len(self.mColors) ],
                                  ecolor = "black",
                                  bottom = sums )[0] )

            if self.label and self.label_matrix != None: 
                self.addLabels( xvals, vals, self.label_matrix[:,column] )

            sums += vals
            y += 1

        if len( self.rows ) > 5 or max( [len(x) for x in self.rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( self.rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + self.width / 2., 
                    self.rows,
                    rotation = rotation )

        return self.endPlot( plts, self.columns, path )

class PiePlot(Renderer, Plotter):
    """A pie chart.

    This :class:`Renderer` requires one level:
    entries[dict] 

    If *pie-first-is-total* is set, the first entry
    is assumed to be the total and all the other values
    are subtracted. It is renamed by the value of *pie-first-is-total*.
    """
    options = Matrix.options + Plotter.options +\
        (('pie-min-percentage', directives.unchanged),
         ('pie-first-is-total', directives.unchanged), )

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.mPieMinimumPercentage = float( kwargs.get("pie-min-percentage", 0 ))

        self.mFirstIsTotal = kwargs.get( "pie-first-is-total", None )

        self.sorted_headers = odict()

    def render( self, work, path ):
        
        self.startPlot()

        for x in work.keys(): 
            if x not in self.sorted_headers: 
                self.sorted_headers[x] = len(self.sorted_headers)

        sorted_vals = [0] * len(self.sorted_headers)

        for key, value in work.iteritems():
            sorted_vals[self.sorted_headers[key]] = value

        labels = self.sorted_headers.keys()

        # subtract others from total - rest
        if self.mFirstIsTotal:
            sorted_vals[0] -= sum(sorted_vals[1:])
            if sorted_vals[0] < 0: raise ValueError( "option first-is-total used, but first < rest" )
            labels[0] = self.mFirstIsTotal

        return self.endPlot( plt.pie( sorted_vals, labels = labels ), None, path )

class MatrixPlot(Matrix, PlotterMatrix):
    """Render a matrix as a matrix plot.
    """
    options = Matrix.options + PlotterMatrix.options

    def __init__(self, *args, **kwargs):
        Matrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def render( self, work, path ):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix( work )
        self.debug("building matrix finished")
        return self.plot( matrix, rows, columns, path )

class HintonPlot(Matrix, PlotterHinton):
    """Render a matrix as a hinton plot.

    Draws a Hinton diagram for visualizing a weight matrix. 

    The size of a box reflects the weight.

    This class adds the following options to the :term:`report` directive:

       :term:`colours`: colour boxes according to value.

    """
    options = Matrix.options + PlotterHinton.options +\
        ( ('colours', directives.unchanged), 
          )

    # column to use for error bars
    colour = None

    def __init__(self, *args, **kwargs):
        Matrix.__init__(self, *args, **kwargs )
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

    nlevels = 2
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render(self, work, path ):

        self.startPlot()

        plts, legend = [], []
        all_data = []

        for line, data in work.iteritems():

            assert len(data) == 1, "multicolumn data not supported yet: %s" % str(data)

            for label, values in data.iteritems():
                assert Utils.isArray( values ), "work is of type '%s'" % values
                d = [ x for x in values if x != None ]
                if len(d) > 0:
                    all_data.append( d )
                    legend.append( "/".join((line,label)))

        plts.append( plt.boxplot( all_data ) )
        
        if len( legend ) > 5 or max( [len(x) for x in legend] ) >= 8 : 
            rotation = "vertical"
        else: 
            rotation = "horizontal"

        plt.xticks( [ x + 1 for x in range(0,len(legend)) ],
                    legend,
                    rotation = rotation,
                    fontsize="8" )

        return self.endPlot( plts, None, path )

class ScatterPlot(Renderer, Plotter):
    """Scatter plot.

    The different tracks will be displayed with different colours.

    This :class:`Renderer` requires two levels:
    track[dict] / coords[dict]
    """
    options = Renderer.options + Plotter.options
    
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


    def render(self, work, path ):
        
        self.startPlot()
        
        nplotted = 0

        plts, legend = [], []
        xlabels, ylabels = [], []

        for label, coords in work.iteritems():
            
            assert len(coords) >= 2, "expected at least two arrays, got %i" % len(coords)

            xlabel, ylabel = coords.keys()[:2]
            xvals, yvals = Stats.filterNone( coords.values()[:2])

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

            nplotted += 1
            
            xlabels.append( xlabel )
            ylabels.append( ylabel )
            
        plt.xlabel( "-".join( set(xlabels) ) )
        plt.ylabel( "-".join( set(ylabels) ) )
        
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

        assert len(work) >= 3, "expected at least three arrays, got %i: %s" % (len(work), work.keys())
        
        xlabel, ylabel, zlabel = work.keys()[:3]
        xvals, yvals, zvals = Stats.filterNone( work.values()[:3])

        if len(xvals) == 0 or len(yvals) == 0 or len(zvals) == 0: 
            raise ValueError("no data" )

        if self.zrange:
            vmin, vmax = self.zrange
            zvals = np.array( zvals )
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

