"""Mixin classes for Renderers that plot.
"""

import os, sys, re

import matplotlib
import matplotlib.backends
import matplotlib.pyplot as plt
import numpy
import CorrespondenceAnalysis

class Plotter:
    """Base class for Renderers that do simple 2D plotting.

    This mixin class provides convenience function for :class:`Renderer.Renderer`
    classes that do 2D plotting.

    The base class takes care of counting the plots created,
    provided that the methods :meth:`startPlot` and :meth:`endPlot`
    are called appropriately. It then inserts the appropriate place holders.

    This class adds the following options to the :term:`render` directive:

       :term:`logscale`: apply logscales one or more axes.

       :term:`xtitle`: add a label to the X axis

       :term:`ytitle`: add a label to the Y axis

       :term:`title`: add a title to the plot

       :term:`legend-location`: specify the location of the legend

       :term:`as-lines`: do not plot symbols

       :term:`xrange`: restrict plot a part of the x-axis

       :term:`yrange`: restrict plot a part of the y-axis

    """

    mLegendFontSize = 8
    # number of chars to use to reduce legend font size
    mMaxLegendSize = 100

    def __init__(self, tracker ):
        self.mTracker = tracker

    def prepare(self, *args, **kwargs):
        """parse option arguments."""

        self.mFormat = "%i"
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

        try: self.mXRange = map(float, kwargs["xrange"].split(","))
        except: self.mXRange = None

        try: self.mYRange = map(float, kwargs["yrange"].split(","))
        except: self.mYRange = None

    def startPlot( self, data ):
        """prepare everything for a plot."""

        self.mFigure +=1 
        plt.figure( self.mFigure )
        
        if self.mTitle:  plt.title( self.mTitle )
        if self.mXLabel: plt.xlabel( self.mXLabel )
        if self.mYLabel: plt.ylabel( self.mYLabel )

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

    def endPlot( self, plts = None, legends = None ):
        """close a plot.

        Returns a list of restructured text with place holders for the current figure.
        """

        if self.mXRange: plt.xlim( self.mXRange )
        if self.mYRange: plt.ylim( self.mYRange )

        if self.mLogScale:
            if "x" in self.mLogScale:
                plt.gca().set_xscale('log')
            if "y" in self.mLogScale:
                plt.gca().set_yscale('log')

                
        if self.mLegendLocation != "none" and plts and legends:
            maxlen = max( [ len(x) for x in legends ] )
            # legends = self.wrapText( legends )

            if self.mLegendLocation == "outer":
                legend = outer_legend( plts, legends )
            else:
                legend = plt.figlegend( plts, 
                                        legends,
                                        loc = self.mLegendLocation )

            # smaller font size for large legends
            if maxlen > self.mMaxLegendSize:
                ltext = legend.get_texts() # all the text.Text instance in the legend
                plt.setp(ltext, fontsize='small') 
            
        return [ "## Figure %i ##" % self.mFigure, "" ]

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
    
    This class adds the following options to the :term:`render` directive:
    
       :term:`colorbar-format`: numerical format for the colorbar.

       :term:`palette`: numerical format for the colorbar.

       :term:`zrange`: restrict plot a part of the z-axis.

    """

    mFontSize = 8

    # after # characters, split into two
    # lines
    mSplitHeader = 20
    mFontSizeSplit = 6

    # separators to use to split text
    mSeparators = " :_"

    def __init__(self, *args, **kwargs ):
        Plotter.__init__(self, *args, **kwargs)

    def prepare( self,*args, **kwargs ):
        Plotter.prepare(self, *args, **kwargs)

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        try: self.mZRange = map(float, kwargs["zrange"].split(",") )
        except KeyError: self.mZRange = None

        self.mReversePalette = "reverse-palette" in kwargs

    def buildHeaders( self, headers ):
        """build headers. Long headers are split using
        the \frac mathtext directive (mathtext does not
        support multiline equations.

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

    def plotMatrix( self, matrix, row_headers, col_headers ):

        self.startPlot( matrix )

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

        plt.imshow(matrix,
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

        xfontsize = self.mFontSize 
        yfontsize = self.mFontSize 

        # determine fontsize for labels
        xfontsize, col_headers = self.buildHeaders( col_headers )
        yfontsize, row_headers = self.buildHeaders( row_headers )

        plt.xticks( [ offset + x for x in range(len(col_headers)) ],
                      col_headers,
                      rotation="vertical",
                      fontsize=xfontsize )

        plt.yticks( [ offset + y for y in range(len(row_headers)) ],
                      row_headers,
                      fontsize=yfontsize )

        plt.colorbar( format = self.mBarFormat)        

        self.rescaleForVerticalLabels( col_headers, cliplen = 12 )

        return self.endPlot()

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
