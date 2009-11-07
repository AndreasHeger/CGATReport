import os, sys, re, shelve, traceback, cPickle, types, itertools

from Plotter import *
from Tracker import *

from math import *

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers

import bsddb.db

import numpy
import numpy.ma
# so that arange is available in eval
from numpy import *

import sqlalchemy

import Stats
import Histogram
import collections

from DataTypes import *
from ResultBlock import ResultBlock, ResultBlocks
import odict

# Some renderers will build several objects.
# Use these two rst levels to separate individual
# entries. Set to None if not separation.
SECTION_TOKEN = "@"
SUBSECTION_TOKEN = "^"

VERBOSE=True

from logging import warn, log, debug, info
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( "sphinxreport.log", "a" ) )

# for cachedir
cachedir = None
if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

def unique( iterables ):
    s = set()
    for x in iterables:
        if x not in s:
            yield x
            s.add(x)

class Renderer(object):
    """Base class of renderers that render data into restructured text.

    The subclasses define how to render the data by overloading the
    :meth:`render` method.

    When called, a Renderer and its subclasses will return blocks of
    restructured text. Images are automatically collected from matplotlib
    and inserted at place-holders in the format ``## Figure x ##``, where
    ``x`` is number of the figure.

    For example, a renderer might return two figures as::

       return [ "## Figure 1 ##", "## Figure 2 ##" ]``

    or just some text::

       return [ "text element 1", "text element 2" ]

    The base class implements querying the :attr:`mTracker` for tracks and 
    slices and then asking the tracker for data grouped by tracks or slices.

    This class adds the following options to the :term:`render` directive.

       :term:`groupby`: group data by :term:`track` or :term:`slice`.

    """

    # required levels in nested dictionary
    nlevels = None

    def __init__(self, tracker, *args, **kwargs ):
        """create an Renderer object using an instance of 
        a :class:`Tracker.Tracker`.
        """

        debug("starting renderer '%s'")

        try: self.mLayout = kwargs["layout"]
        except KeyError: self.mLayout = "column"

        try: self.mGroupBy = kwargs["groupby"]
        except KeyError: self.mGroupBy = "slice"

        self.mTracker = tracker

    def __call__(self):
        return None

    def getLabels( self, data ):
        '''extract labels from data.

        returns a list of list with all labels within
        the nested dictionary of data.
        '''
        labels = []
        
        this_level = [data,]

        while 1:
            l, next_level = [], []
            for x in [ x for x in this_level if hasattr( x, "keys")]:
                l.extend( x.keys() )
                next_level.extend( x.values() )
            if not l: break
            labels.append( list(unique(l)) )
            this_level = next_level

        debug( "%s: found the following labels: %s" % (str(self),labels))
        return labels

    def getLeaf( self, data, path ):
        '''get leaf in hierarchy at path.'''
        work = data
        for x in path:
            try:
                work = work[x]
            except KeyError:
                work = None
                break
        return work

    def __call__(self, data, title ):
        '''iterate over leaves in data structure.

        and call ``render`` method.
        '''
        if self.nlevels == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        labels = self.getLabels( data )        
        assert len(labels) >= self.nlevels, "expected at least %i levels - got %i" % (self.nlevels, len(labels))
        
        paths = list(itertools.product( *labels[:-self.nlevels] ))
        
        result = ResultBlocks( title = title )

        for path in paths:
            subtitle = "-".join( path )
            work = self.getLeaf( data, path )
            if not work: continue
            result.extend( self.render( work, path ) )

        return result
            
class RendererTable( Renderer ):
    '''a basic table. 

    Values are either text or converted to text.
    '''
    def __init__( self, *args, **kwargs ):
        Renderer.__init__(self, *args, **kwargs )
        self.mTranspose = "transpose" in kwargs

    def getHeaders( self, data ):
        """return a list of headers and a mapping of header to column.
        """
        # preserve the order of columns
        column_headers = {}
        sorted_headers = []

        try:
            for row, r in data.iteritems():
                for column, c in r.iteritems():
                     for header, value in c.iteritems():
                        if header not in column_headers: 
                            column_headers[header] = len(column_headers)
                            sorted_headers.append(header)
        except AttributeError:
            raise ValueError("mal-formatted data - RendererTable expected three level dictionary, got %s." % str(data) )

        return sorted_headers, column_headers

    def buildTable( self, data ):
        """build table from data.

        If there is more than one :term:`column`, additional subrows
        are added for each.

        returns matrix, row_headers, col_headers
        """
        if len(data) == 0: return None, None, None

        labels = self.getLabels( data )        
        assert len(labels) >= 2, "expected at least two levels for building table"

        col_headers = [""] * (len(labels)-2) + labels[-1]
        ncols = len(col_headers)

        row_headers = []
        paths = list(itertools.product( *labels[1:-1] ))                
        npaths = len(paths)
        for x in labels[0]: 
            row_headers.extend( [x] + [""] * (npaths-1) )
        nrows = len(row_headers)
        
        offset = len(labels)-2
        matrix = [ [""] * ncols for x in range(nrows) ]

        debug( "RendererTable: creating table with %i rows and %i columns" % (len(row_headers), len(col_headers)))
        ## the following can be made more efficient
        ## by better use of indices
        for x,row in enumerate(labels[0]):
            for xx, path in enumerate(paths):
                work = self.getLeaf( data, (row,) + path )
                if not work: continue
                for y, column in enumerate(labels[-1]):
                    matrix[x*npaths+xx][y+offset] = str(work[column])
                for z, p in enumerate(path):
                    matrix[x*npaths+xx][z] = p
        if self.mTranspose:
            row_headers, col_headers = col_headers, row_headers
            matrix = zip( *matrix )

        return matrix, row_headers, col_headers

    def __call__(self, data, title = None):

        lines = []
        matrix, row_headers, col_headers = self.buildTable( data )
        if matrix == None: return lines

        if not title: mytitle = "title"
        else: mytitle = title

        lines.append( ".. csv-table:: %s" % mytitle )
        lines.append( '   :header: "", "%s" ' % '","'.join( col_headers ) )
        lines.append( '' )

        for header, line in zip( row_headers, matrix ):
            lines.append( '   "%s","%s"' % (header, '","'.join( line ) ) )

        lines.append( "") 

        return ResultBlocks( ResultBlock( "\n".join(lines), title = title) )

class RendererGlossary( RendererTable ):
    """output a table in the form of a glossary."""

    def __call__(self, data, title = None):

        lines = []
        matrix, row_headers, col_headers = self.buildTable( data )

        if matrix == None: return lines

        lines.append( ".. glossary::" )

        lines.append( "") 

        for header, line in zip( row_headers, matrix ):
            txt = "\n".join( line )
            txt = "\n      ".join( [ x.strip() for x in txt.split("\n" ) ] )
            lines.append( '   %s\n      %s' % ( header, txt ) )

        lines.append( "") 

        return ResultBlocks( "\n".join(lines), title = title )


class RendererMatrix(Renderer):    
    """A table with numerical columns.

    It implements column-wise and row-wise transformations.

    This class adds the following options to the :term:`render` directive.

        :term:`transform-matrix`: apply a matrix transform. Possible choices are:

           * *correspondence-analysis*: use correspondence analysis to permute rows/columns 
           * *normalized-column-total*: normalize by column total
           * *normalized-column-max*: normalize by column maximum
           * *normalized-row-total*: normalize by row total
           * *normalized-row-max*: normalize by row maximum
           * *normalized-total*: normalize over whole matrix
           * *normalized-max*: normalize over whole matrix
           * filter-by-rows: only take columns that are also present in rows
           * filter-by-cols: only take columns that are also present in cols
           * square: make square matrix (only take rows and columns present in both)
           * *add-row-total* : add the row total at the bottom
           * *add-column-total* : add the column total as a last column

    Requires two levels:
    rows[dict] / columns[dict]
    """

    nlevels = 2

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

        self.mMapKeywordToTransform = {
        "correspondence-analysis": self.transformCorrespondenceAnalysis,
        "transpose": self.transformTranspose,
        "normalized-row-total" : self.transformNormalizeRowTotal,
        "normalized-row-max" : self.transformNormalizeRowMax,
        "normalized-col-total" : self.transformNormalizeColumnTotal,
        "normalized-col-max" : self.transformNormalizeColumnMax ,
        "normalized-total" : self.transformNormalizeTotal,
        "normalized-max" : self.transformNormalizeMax,
        "filter-by-rows" : self.transformFilterByRows,
        "filter-by-cols" : self.transformFilterByColumns,
        "square" : self.transformSquare,
        "add-row-total" : self.transformAddRowTotal,
        "add-column-total" : self.transformAddColumnTotal,
        }
        
        self.mFormat = "%i"

        self.mConverters = []        
        if "transform-matrix" in kwargs:
            for kw in [x.strip() for x in kwargs["transform-matrix"].split(",")]:
                if kw.startswith( "normalized" ): self.mFormat = "%6.4f"
                try:
                    self.mConverters.append( self.mMapKeywordToTransform[ kw ] )
                except KeyError:
                    raise ValueError("unknown matrix transformation %s" % kw )

    def transformAddRowTotal( self, matrix, row_headers, col_headers ):
        raise NotImplementedError

    def transformAddColumnTotal( self, matrix, row_headers, col_headers ):
        raise NotImplementedError

    def transformFilterByRows( self, matrix, row_headers, col_headers ):
        """only take columns that are also present in rows"""
        take = [ x for x in xrange( len(col_headers) ) if col_headers[x] in row_headers ]
        return matrix.take( take, axis=1), row_headers, [col_headers[x] for x in take ]

    def transformFilterByColumns( self, matrix, row_headers, col_headers ):
        """only take rows that are also present in columns"""
        take = [ x for x in xrange( len(row_headers) ) if row_headers[x] in col_headers ]
        return matrix.take( take, axis=0), [row_headers[x] for x in take ], col_headers 

    def transformSquare( self, matrix, row_headers, col_headers ):
        """only take rows and columns that are present in both giving a square matrix."""
        take = set(row_headers).intersection( set(col_headers) )
        row_indices = [ x for x in range( len(row_headers) ) if row_headers[x] in take ]
        col_indices = [ x for x in range( len(col_headers) ) if col_headers[x] in take ]
        m1 = matrix.take( row_indices, axis=0)
        m2 = m1.take( col_indices, axis=1)

        return m2, [row_headers[x] for x in row_indices], [col_headers[x] for x in col_indices]

    def transformTranspose( self, matrix, row_headers, col_headers ):
        """transpose the matrix."""
        return numpy.transpose( matrix ), col_headers, row_headers

    def transformCorrespondenceAnalysis( self, matrix, row_headers, col_headers ):
        """apply correspondence analysis to a matrix.
        """
        try:
            row_indices, col_indices =  CorrespondenceAnalysis.GetIndices( matrix )
        except ValueError, msg:
            return matrix, row_headers, col_headers            

        map_row_new2old = numpy.argsort(row_indices)
        map_col_new2old = numpy.argsort(col_indices)
        
        matrix, row_headers, col_headers =  CorrespondenceAnalysis.GetPermutatedMatrix( matrix,
                                                                                        map_row_new2old,
                                                                                        map_col_new2old,
                                                                                        row_headers = row_headers,
                                                                                        col_headers = col_headers)



        return matrix, row_headers, col_headers

    def transformNormalizeTotal( self, matrix, rows, cols ):
        """normalize a matrix by the total.

        Returns the normalized matrix.
        """
        t = matrix.sum()
        matrix /= t
        return matrix, rows, cols

    def transformNormalizeMax( self, matrix, rows, cols ):
        """normalize a matrix by the max.

        Returns the normalized matrix.
        """
        t = matrix.max()
        matrix /= t
        return matrix, rows, cols

    def transformNormalizeRowTotal( self, matrix, rows, cols ):
        """normalize a matrix row by the row total.

        Returns the normalized matrix.
        """
        nrows, ncols = matrix.shape

        for x in range(nrows) :
            s = sum(matrix[x,:])
            if m != 0:
                for y in range(ncols):
                    matrix[x,y] /= s
        return matrix, rows, cols

    def transformNormalizeRowMax( self, matrix, rows, cols ):
        """normalize a matrix row by the row maximum.

        Returns the normalized matrix.
        """
        nrows, ncols = matrix.shape

        for x in range(nrows) :
            m = max(matrix[x,:])
            if m != 0:
                for y in range(ncols):
                    matrix[x,y] /= m
        return matrix, rows, cols

    def transformNormalizeColumnTotal( self, matrix, rows, cols ):
        """normalize a matrix by the column total.

        Returns the normalized matrix."""
        nrows, ncols = matrix.shape
        totals = [sum( matrix[:,y] ) for y in range(ncols) ]
        for x in range(nrows):
            for y in range(ncols):
                m = totals[y]
                if m != 0: matrix[x,y] /= m
        return matrix, rows, cols

    def transformNormalizeColumnMax( self, matrix, rows, cols ):
        """normalize a matrix by the column maximum

        Returns the normalized matrix.
        """
        nrows, ncols = matrix.shape

        for y in range(ncols) :
            m = max(matrix[:,y])
            if m != 0:
                for x in range(nrows):
                    matrix[x,y] /= m
        return matrix, rows, cols

    def buildMatrix( self, work, missing_value = 0 ):
        """build a matrix from data.

        This method will also apply conversions.

        Returns a list of tuples (title, matrix, rows, colums).
        """

        labels = self.getLabels( work )
        levels = len(labels )
        if levels != 2: raise ValueError( "expected two levels" )

        rows, columns = labels

        matrix = numpy.array( [missing_value] * (len(rows) * len(columns) ), numpy.float)
        matrix.shape = (len(rows), len(columns) )
        for x,row in enumerate(rows):
            for y, column in enumerate(columns):
                try:
                    matrix[x,y] = work[row][column]
                except KeyError:
                    # ignore missing and malformatted data
                    pass
                except ValueError:
                    raise ValueError( "malformatted data: expected scalar, got '%s'" % str(work[row][column]) )
                
        if self.mConverters:
            for converter in self.mConverters: 
                matrix, rows, columns = converter(matrix, rows, columns)

        return matrix, rows, columns

    def render( self, work, path ):
        """render the data.
        """
        results = ResultBlocks( title = path )
        matrix, rows, columns = self.buildMatrix( work )

        lines = []
        if len(rows) == 0: return lines

        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "track","%s" ' % '","'.join( columns ) )
        lines.append( '')
        for x in range(len(rows)):
            lines.append( '   "%s","%s"' % (rows[x], '","'.join( [ self.mFormat % x for x in matrix[x,:] ] ) ) )
        lines.append( "") 
        if not path: subtitle = ""
        else: subtitle = path
        results.append( ResultBlock( "\n".join(lines), title = subtitle ) )

        return results

class RendererLinePlot(Renderer, Plotter):        
    '''create a line plot.

    This :class:`Renderer` requires three levels:
    line / data / coords
    '''
    nlevels = 3

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render(self, work, path ):
        
        self.startPlot()

        plts, legend = [], []
        xlabels, ylabels = [], []
        nplotted = 0

        for line, data in work.iteritems():

            assert len(data) == 1, "multicolumn data not supported yet: %s" % str(data)

            for label, coords in data.iteritems():
                s = self.mSymbols[nplotted % len(self.mSymbols)]

                # get and transform x/y values

                xlabel, ylabel = coords.keys()
                xvals, yvals = coords.values()

                plts.append(plt.plot( xvals,
                                      yvals,
                                      s ) )
                
                legend.append( "/".join((line,label) ))
                nplotted += 1

                xlabels.append(xlabel)
                ylabels.append(ylabel)

        plt.xlabel( "-".join( set(xlabels) ) )
        plt.ylabel( "-".join( set(ylabels) ) )
        
        return self.endPlot( plts, legend, path )

class RendererBarPlot( RendererMatrix, Plotter):
    """A plot with interleaved bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        matrix, rows, columns = self.buildMatrix( work )

        plts = []

        self.startPlot()

        xvals = numpy.arange( 0, len(rows) )

        # plot by row
        y = 0
        for x,header in enumerate(columns):
            
            vals = matrix[:,x]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals, 
                                  vals,
                                  self.mWidth, 
                                  color = self.mColors[ y % len(self.mColors) ],
                                  )[0] )
            
            y += 1

        if len( rows ) > 5 or max( [len(x) for x in rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + 0.5, rows, rotation = rotation )

        return self.endPlot( plts, columns, path )

class RendererInterleavedBarPlot(RendererBarPlot):
    """A plot with interleaved bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    def __init__(self, *args, **kwargs):
        RendererBarPlot.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        matrix, rows, columns = self.buildMatrix( work )

        width = 1.0 / (len(columns) + 1 )
        plts = []

        self.startPlot()

        xvals = numpy.arange( 0, len(rows) )
        offset = width / 2.0

        # plot by row
        y = 0
        for x,header in enumerate(columns):
            
            vals = matrix[:,x]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals + offset, 
                                  vals,
                                  width,
                                  color = self.mColors[ y % len(self.mColors) ],
                                  )[0] )
            
            offset += width
            y += 1

        if len( rows ) > 5 or max( [len(x) for x in rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + 0.5, rows, rotation = rotation )

        return self.endPlot( plts, columns, path )
           
class RendererStackedBarPlot(RendererBarPlot ):
    """A plot with stacked bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """
    def __init__(self, *args, **kwargs):
        RendererBarPlot.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        matrix, rows, columns = self.buildMatrix( work )
        
        self.startPlot( )

        plts = []

        xvals = numpy.arange( (1.0 - self.mWidth) / 2., len(rows) )
        sums = numpy.zeros( len(rows), numpy.float )

        y = 0
        for x,header in enumerate(columns):

            vals = matrix[:,x]            

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0
                
            plts.append( plt.bar( xvals, 
                                  vals, 
                                  self.mWidth, 
                                  color = self.mColors[ y % len(self.mColors) ],
                                  bottom = sums )[0] )
            
            sums += vals
            y += 1

        if len( rows ) > 5 or max( [len(x) for x in rows] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( rows )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + self.mWidth / 2., 
                    rows,
                    rotation = rotation )

        return self.endPlot( plts, columns, path )

class RendererPiePlot(Renderer, Plotter):
    """A pie chart.

    This :class:`Renderer` requires one level:
    entries[dict] 
    """
    nlevels = 1
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        self.mFormat = "%i"

        try: self.mPieMinimumPercentage = float(kwargs["pie-min-percentage"])
        except KeyError: self.mPieMinPercentage = 0

        self.sorted_headers = odict.OrderedDict()

    def render( self, work, path ):
        
        self.startPlot()

        for x in work.keys(): 
            if x not in self.sorted_headers: 
                self.sorted_headers[x] = len(self.sorted_headers)

        sorted_vals = [0] * len(self.sorted_headers)

        for key, value in work.iteritems():
            sorted_vals[self.sorted_headers[key]] = value
        
        return self.endPlot( plt.pie( sorted_vals, labels = self.sorted_headers.keys() ), None, path )

class RendererMatrixPlot(RendererMatrix, PlotterMatrix):
    """Render a matrix as a matrix plot.
    """

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )
        self.mFormat = "%i"

    def render( self, work, path ):
        """render the data."""

        matrix, rows, columns = self.buildMatrix( work )
        return self.plot( matrix, rows, columns, path )

class RendererHintonPlot(RendererMatrix, PlotterHinton):
    """Render a matrix as a hinton plot.
    """

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )
        self.mFormat = "%i"

    def render( self, work, path ):
        """render the data."""

        matrix, rows, columns = self.buildMatrix( work )
        return self.plot( matrix, rows, columns, path )

class RendererBoxPlot(Renderer, Plotter):        
    """Write a set of box plots.
    
    This :class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    
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
                assert isArray( values ), "work is of type '%s'" % values
                all_data.append( [ x for x in values if x != None ] )
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

class RendererScatterPlot(Renderer, Plotter):
    """Scatter plot.

    The different tracks will be displayed with different colours.

    This :class:`Renderer` requires two levels:
    track[dict] / coords[dict]
    """
    
    nlevels = 2

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def render(self, work, path ):
        
        self.startPlot()
        
        nplotted = 0

        plts, legend = [], []
        xlabels, ylabels = [], []

        for label, coords in work.iteritems():
            
            assert len(coords) >= 2, "expected at least two arrays, got %i" % len(coords)

            xlabel, ylabel = coords.keys()[:2]
            xvals, yvals = coords.values()[:2]

            marker = self.mMarkers[nplotted % len(self.mMarkers)]
            color = self.mColors[nplotted % len(self.mColors)]
            if len(xvals) == 0 or len(yvals) == 0: continue
            plts.append(plt.scatter( xvals,
                                     yvals,
                                     marker = marker,
                                     c = color) )
            legend.append( label )

            nplotted += 1
            
            xlabels.append( xlabel )
            ylabels.append( ylabel )
            
        plt.xlabel( "-".join( set(xlabels) ) )
        plt.ylabel( "-".join( set(ylabels) ) )
        
        return self.endPlot( plts, legend, path )

class RendererScatterPlotWithColor( Renderer, Plotter ):
    """Scatter plot with individual colors for each dot.

    This class adds the following options to the :term:`render` directive:

       :term:`colorbar-format`: numerical format for the colorbar.

       :term:`palette`: numerical format for the colorbar.

       :term:`zrange`: restrict plot a part of the z-axis.

    This :class:`Renderer` requires one level:

    coords[dict]
    """

    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        try: self.mZRange = map(float, kwargs["zrange"].split(",") )
        except KeyError: self.mZRange = None

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
        xvals, yvals, zvals = work.values()[:3]
        if len(xvals) == 0 or len(yvals) == 0 or len(zvals) == 0: 
            raise ValueError("no data" )

        if self.mZRange:
            vmin, vmax = self.mZRange
            zvals[ zvals < vmin ] = vmin
            zvals[ zvals > vmax ] = vmax
        else:
            vmin, vmax = None, None

        plts.append(plt.scatter( xvals,
                                 yvals,
                                 c = zvals,
                                 vmax = vmax,
                                 vmin = vmin ) )
            
        plt.xlabel( xlabel )
        plt.ylabel( ylabel )

        cb = plt.colorbar( format = self.mBarFormat)        
        cb.ax.set_xlabel( zlabel )

        return self.endPlot( plts, None, path )

class RendererMultiHistogramPlot(Renderer, Plotter):
    """Render histogram data as plot.

    The data should be already histgrammed and the first
    column is taken as the bins.

    Requires :class:`DataTypes.MultipleColumnData`.
    """

    bin_marker = "left"

    mRequiredType = type( MultipleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def prepare(self, *args, **kwargs ):

        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )
        
    def render(self, data):
        """returns a placeholder."""
        
        blocks = []

        for track, vv in data:

            self.startPlot()
            headers, columns = vv

            # get and transform x/y values
            xvals = columns[0]

            plts, legend = [], []
            nplotted = 0
            for y in range( 1, len(columns) ):
                s = self.mSymbols[nplotted % len(self.mSymbols)]        
                yvals = columns[y]
                plts.append(plt.plot( xvals, yvals, s ) )
                legend.append( headers[y] )
                nplotted += 1

            blocks.extend( self.endPlot( plts, legend, title = track ) )

        return blocks

        

