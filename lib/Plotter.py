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
    def __init__(self, tracker ):
        self.mTracker = tracker

    def prepare(self, *args, **kwargs):
        """parse option arguments."""

        self.mFormat = "%i"
        self.mFigure = 0
        self.mColors = "bgrcmk"
        self.mSymbols = ["g-D","b-h","r-+","c-+","m-+","y-+","k-o","g-^","b-<","r->","c-D","m-h"]
        self.mMarkers = "so^>dph8+x"

        try: self.mLogScale = kwargs["logscale"]
        except KeyError: self.mLogScale = None

        try: self.mTitle = kwargs["title"]
        except KeyError: self.mTitle = None

        try: self.mXTitle = kwargs["xtitle"]
        except KeyError: self.mXLabel = self.mTracker.getXLabel()

        try: self.mYLabel = kwargs["ytitle"]
        except KeyError: self.mYLabel = self.mTracker.getYLabel()

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
            if self.mLegendLocation == "outer":
                outer_legend( plts, legends )
            else:
                plt.figlegend( plts, 
                               legends,
                               loc = self.mLegendLocation )

        return [ "## Figure %i ##" % self.mFigure, "" ]

    def rescaleForVerticalLabels( self, labels, offset = 0.02, cliplen = 6 ):
        """rescale current plot so that vertical labels are displayed properly.

        In some plots the labels are clipped if the labels are vertical labels on the X-axis.
        This is a heuristic hack and is not guaranteed to always work.
        """
        # rescale plotting area if labels are more than 6 characters
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

    def plotMatrix( self, matrix, row_headers, col_headers ):

        self.startPlot( matrix )

        nrows, ncols = matrix.shape
        if self.mZRange:
            vmin, vmax = self.mZRange
            for x in range(nrows):
                for y in range(ncols):
                    if matrix[x,y] < self.mZRange[0]:
                        matrix[x,y] = self.mZRange[0]
                    if matrix[x,y] > self.mZRange[1]:
                        matrix[x,y] = self.mZRange[1]
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

        plt.xticks( [ offset + x for x in range(len(col_headers)) ],
                      col_headers,
                      rotation="vertical",
                      fontsize="8" )

        plt.yticks( [ offset + y for y in range(len(row_headers)) ],
                      row_headers,
                      fontsize="8" )

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
