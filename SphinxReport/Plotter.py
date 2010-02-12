"""Mixin classes for Renderers that plot.
"""

import os, sys, re, math

import matplotlib
import matplotlib.backends
import matplotlib.pyplot as plt
import numpy

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks

class Plotter:
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

    def __init__(self, *args, **kwargs ):
        """parse option arguments."""

        self.mFigure = 0
        self.mColors = "bgrcmk"
        self.mSymbols = ["g-D","b-h","r-+","c-+","m-+","y-+","k-o","g-^","b-<","r->","c-D","m-h"]
        self.mMarkers = "so^>dph8+x"
        self.mXLabel = None
        self.mYLabel = None

        try: self.mLogScale = kwargs["logscale"]
        except KeyError: self.mLogScale = None

        try: self.mTitle = kwargs["title"]
        except KeyError: self.mTitle = None

        if "add-title" in kwargs: self.mAddTitle = True
        else: self.mAddTitle = False

        try: self.mXLabel = kwargs["xtitle"]
        except KeyError: 
            try: self.mXLabel = self.mTracker.getXLabel()
            except AttributeError: self.mXLabel = None

        try: self.mYLabel = kwargs["ytitle"]
        except KeyError: 
            try: self.mYLabel = self.mTracker.getYLabel()
            except AttributeError: self.mYLabel = None

        try: self.mLegendLocation = kwargs["legend-location"]
        except KeyError: self.mLegendLocation = "outer"

        try: self.mWidth = kwargs["width"]
        except KeyError: self.mWidth = 0.50

        self.mAsLines = "as-lines" in kwargs

        if self.mAsLines:
            self.mSymbols = []
            for y in ("-",":","--"):
                for x in "gbrcmyk":
                    self.mSymbols.append( y+x )

        def _parseRanges(r):
            if not r: return r
            r = [ x.strip() for x in r.split(",")]
            if r[0] == "": r[0] = None
            else: r[0] = float(r[0])
            if r[1] == "": r[1] = None
            else: r[1] = float(r[1])
            return r

        self.mXRange = _parseRanges(kwargs.get("xrange", None ))
        self.mYRange = _parseRanges(kwargs.get("yrange", None ))

        def setupMPLOption( key ):
            options = {}
            try: 
                for k in kwargs[ key ].split(";"):
                    key,val = k.split("=")
                    # convert unicode to string
                    options[str(key)] = eval(val)
            except KeyError: 
                pass
            return options

        self.mMPLFigureOptions = setupMPLOption( "mpl-figure" )
        self.mMPLLegendOptions = setupMPLOption( "mpl-legend" )
        self.mMPLSubplotOptions = setupMPLOption( "mpl-subplot" )
        self.mMPLRC = setupMPLOption( "mpl-rc" )

    def startPlot( self, **kwargs ):
        """prepare everything for a plot."""

        self.mFigure +=1 

        # go to defaults
        matplotlib.rcdefaults()
        # set parameters
        matplotlib.rcParams.update(self.mMPLRC )
        
        self.mCurrentFigure = plt.figure( num = self.mFigure, **self.mMPLFigureOptions )

        if self.mTitle:  plt.title( self.mTitle )

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
        if self.mLogScale:
            if "x" in self.mLogScale:
                plt.gca().set_xscale('log')
            if "y" in self.mLogScale:
                plt.gca().set_yscale('log')

        if self.mXRange:
            plt.xlim( self.mXRange )
        if self.mYRange:
            plt.ylim( self.mYRange )
            
        if self.mAddTitle: plt.suptitle( "/".join(path) )

        blocks = ResultBlocks( ResultBlock( "\n".join( ("#$mpl %i$#" % (self.mFigure-1), "")), title = "/".join(path) ) )

        legend = None
        maxlen = 0

        if self.mLegendLocation != "none" and plts and legends:

            maxlen = max( [ len(x) for x in legends ] )
            # legends = self.wrapText( legends )

            assert len(plts) == len(legends)
            if self.mLegendLocation == "outer":
                legend = outer_legend( plts, legends )
            else:
                legend = plt.figlegend( plts, 
                                        legends,
                                        loc = self.mLegendLocation,
                                        **self.mMPLLegendOptions )


        if self.mLegendLocation == "extra" and legends:

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

    def __init__(self, *args, **kwargs ):
        Plotter.__init__(self, *args, **kwargs)

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        try: self.mZRange = map(float, kwargs["zrange"].split(",") )
        except KeyError: self.mZRange = None

        try: self.mMaxRows = kwargs["max-rows"]
        except KeyError: self.mMaxRows = 20

        try: self.mMaxCols = kwargs["max-cols"]
        except KeyError: self.mMaxCols = 20

        self.mReversePalette = "reverse-palette" in kwargs

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
            
        return plot

    def plot( self,  matrix, row_headers, col_headers, path ):
        '''plot matrix. 

        Large matrices are split into several plots.
        '''
        self.startPlot()

        nrows, ncols = matrix.shape
        if self.mZRange:
            vmin, vmax = self.mZRange
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
            # do not split small or symmetric matrices
            self.plotMatrix( matrix, row_headers, col_headers, vmin, vmax, color_scheme )
            try:
                plt.colorbar( format = self.mBarFormat)        
            except AttributeError:
                # fails for hinton plots
                pass

            plots, labels = None, None
            self.rescaleForVerticalLabels( col_headers, cliplen = 12 )

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
                self.mLegendLocation = "extra"
                plt.subplots_adjust( **self.mMPLSubplotOptions )

        elif split_row:
            if not self.mZRange:
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
            self.mLegendLocation = "extra"
            plt.subplots_adjust( **self.mMPLSubplotOptions )
            plt.colorbar( format = self.mBarFormat)        

        elif split_col:
            if not self.mZRange:
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
            self.mLegendLocation = "extra"
            plt.subplots_adjust( **self.mMPLSubplotOptions )
            plt.colorbar( format = self.mBarFormat)        

        return self.endPlot( plots, labels, path )

class PlotterHinton(PlotterMatrix):
    '''plot a hinton diagram.'''
    
    def __init__(self, *args, **kwargs ):
        Plotter.__init__(self, *args, **kwargs)

    def plotMatrix( self, matrix, row_headers, col_headers, vmin, vmax, color_scheme = None):
        return hinton( matrix )

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
    if 'loc' in kwargs: kwargs.pop('loc')
    leg = plt.legend(loc=(0,0), *args, **kwargs)
    frame = leg.get_frame()
    currentAxes = plt.gca()
    currentAxesPos = currentAxes.get_position()

    # scale plot by the part which is taken by the legend
    plotScaling = 0.75

    # scale the plot
    currentAxes.set_position((currentAxesPos.xmin,
                              currentAxesPos.ymin,
                              currentAxesPos.width * (plotScaling),
                              currentAxesPos.height))

    # set (approximate) x and y coordinates of legend 
    leg._loc = (1 + .05, currentAxesPos.ymin )

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
