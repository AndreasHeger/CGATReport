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
    level = None

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
        if self.level == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        labels = self.getLabels( data )        
        assert len(labels) < self.level, "expected at least %i levels - got %i" % (self.level, len(labels))
        
        paths = list(itertools.product( *labels[:-self.levels] ))
        
        for path in paths:
            subtitle = "-".join( path )
            work = self.getLeaf( data, path )
            if not work: continue
            self.render( work, path )
            
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
        
        nsubrows = len(labels)-2
        for x in labels[0]: row_headers.extend( [x] + [""] * (nsubrows-1) )
        nrows = len(row_headers)
        
        offset = len(labels)-2
        matrix = [ [""] * ncols for x in range(nrows) ]

        ## the following can be made more efficient
        ## by better use of indices
        for x,row in enumerate(labels[0]):
            paths = list(itertools.product( *labels[1:-1] ))
            for xx, path in enumerate(paths):
                work = self.getLeaf( data, (row,) + path )
                if not work: continue
                for y, column in enumerate(labels[-1]):
                    matrix[x*nsubrows+xx][y+offset] = str(work[column])
                for z, p in enumerate(path):
                    matrix[x*nsubrows+xx][z] = p
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

class RendererMyTable(RendererTable):    
    """A table with numerical columns.

    It only implements column wise transformations.

    This class adds the following options to the :term:`render` directive.

       :term:`normalized-max`: normalize data by maximum.

       :term:`normalized-total`: normalize data by total.

       :term:`add-total`: add a total field.

       :term:`transpose`: exchange rows and columns

    Requires :class:`DataTypes.LabeledData`.
    """

    mRequiredType = type( LabeledData( None ) )

    def __init__(self, *args, **kwargs):
        RendererTextTable.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        RendererTextTable.prepare( self, *args, **kwargs )
        self.mFormat = "%i"
        self.mConverters = []
        self.mAddTotal = False

        if "normalized-max" in kwargs:
           self.mConverters.append( self.normalize_max )
           self.mFormat = "%6.4f"
        if "normalized-total" in kwargs:
           self.mConverters.append( self.normalize_total )
           self.mFormat = "%6.4f"
        if "add-total" in kwargs:
            self.mAddTotal = True

    def convertData( self, data ):
        """apply converters to the data.

        The data is a tuple of (track, data) with each data
        a tuple of (header, value).

        The same data structure is returned.

        If there is an error during conversion, values will
        be set to None.
        """
        if self.mConverters == []: return data
        new_data = []
        for track, table in data:
            columns = [x[0] for x in table] 
            if len(columns) == 0: continue
            values = numpy.array( [x[1] for x in table] )
            if not values.any(): 
                warn( "track %s omitted because it is empty" % track )
                continue
            
            try:
                for convert in self.mConverters: values = convert( values )
            except ZeroDivisionError:
                values = [ None ] * len(table) 
            new_data.append( (track, zip( columns, values )) )
        return new_data

    def buildTable( self, data ):
        """build table from data.

        returns matrix, row_headers, col_headers
        """
        data = self.convertData( data )
        if len(data) == 0: return None, None, None

        sorted_col_headers, col_headers = self.getHeaders(data)
        col_headers = sorted_col_headers

        row_headers = []
        matrix = []
        def toValue( d, x):
            try:
                return self.mFormat % d[x]
            except (KeyError, TypeError): 
                return "na"

        if self.mAddTotal:
            for track, d in data:
                dd = dict(d)
                try: total = self.mFormat % sum( dd.values() )
                except TypeError: total = "na"
                matrix.append( [total,] + [ toValue(dd, x) for x in sorted_col_headers ] )
                row_headers.append( track )
            col_headers = ["total"] + col_headers
        else:
            for track, d in data:
                dd = dict(d)
                matrix.append( [ toValue(dd, x) for x in sorted_col_headers ] )
                row_headers.append( track )

        if self.mTranspose:
            row_headers, col_headers = col_headers, row_headers
            matrix = zip( *matrix )

        return matrix, row_headers, col_headers

class RendererMatrix(RendererTable):    
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

    Requires :class:`DataTypes.LabeledData`
    """

    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )

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

    def getHeaders( self, data ):
        """return a list of headers and a mapping of header to column.
        """
        # preserve the order of columns
        column_headers = {}
        sorted_headers = []
        try:
            for row, r in data.iteritems():
                for column, c in r.iteritems():
                    column_headers[column] = len(column_headers)
                    sorted_headers.append(column)
        except AttributeError:
            raise ValueError("mal-formatted data - RendererMatrix expected two level dictionary." )

        return sorted_headers, column_headers

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

    def buildMatrix( self, data, missing_value = 0 ):
        """build a matrix from data.

        This method will also apply conversions.

        Returns a list of tuples (title, matrix, rows, colums).
        """

        matrices = []

        labels = self.getLabels( data )
        levels = len(labels )
        if levels < 2: raise ValueError( "expected at least two levels" )

        rows, columns = labels[-2], labels[-1]
        if levels == 2:
            matrix = numpy.array( [missing_value] * (len(rows) * len(columns) ), numpy.float)
            matrix.shape = (len(rows), len(columns) )
            for x,row in enumerate(rows):
                for y, column in enumerate(columns):
                    try:
                        matrix[x,y] = data[row][column]
                    except KeyError:
                        # ignore missing and malformatted data
                        pass
                    except ValueError:
                        raise ValueError( "malformatted data: expected scalar, got '%s'" % str(data[row][column]) )

            matrices.append( (matrix, rows, columns, None ) )

        else:
            paths = list(itertools.product( *labels[:-2] ))

            for path in paths:
                subtitle = "-".join( path )
                work = self.getLeaf( data, path )
                if not work: continue
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
                            raise ValueError( "malformatted data: expected scalar, got '%s'" % str(data[row][column]) )

                matrices.append( (matrix, rows, columns, subtitle ) )
            
        if self.mConverters:
            new = []
            for matrix, rows, columns, title in matrices:
                for converter in self.mConverters: 
                    matrix, rows, columns = converter(matrix, rows, columns)
                new.append( (matrix, rows, columns, title ) )
            matrices = new

        return matrices

    def __call__( self, data, title ):
        """render the data.
        """

        results = ResultBlocks( title = title )
        chunks = self.buildMatrix(data )

        for matrix, rows, columns, path in chunks:
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
    """create a line plot.
    """

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def __call__(self, data, title ):
        
        self.startPlot()

        plts, legend = [], []

        nplotted = 0
        xlabels = []
        ylabels = []

        labels = self.getLabels( data )
        paths = list(itertools.product( *labels[:-1] ))
        for path in paths:
            work = self.getLeaf( data, path )
            if not work: continue

            s = self.mSymbols[nplotted % len(self.mSymbols)]

            # get and transform x/y values
            assert len(work) == 2, "multicolumn data not supported yet: %s" % str(work)

            xlabel, ylabel = work.keys()
            xvals, yvals = work.values()

            plts.append(plt.plot( xvals,
                                  yvals,
                                  s ) )

            legend.append( "/".join(path) )
            nplotted += 1

            xlabels.append(xlabel)
            ylabels.append(ylabel)

        plt.xlabel( "-".join( set(xlabels) ) )
        plt.ylabel( "-".join( set(ylabels) ) )
        
        return self.endPlot( plts, legend )

class RendererInterleavedBars(RendererTable, Plotter):
    """A barplot with interleaved bars
    """

    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def __call__( self, data, title ):

        matrix, row_headers, col_headers = self.buildTable( data )
        if matrix == None: return lines

        nplotted = 0
        nskipped = 0

        width = 1.0 / (len(row_headers) + 1 )

        legend, plts = [], []

        self.startPlot()

        xvals = numpy.arange( 0, len(col_headers) )
        offset = width / 2.0
        
        y = 0

        # plot by row
        for x,header in enumerate(row_headers):
            
            vals = matrix[x,:]

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

        if len( tracks ) > 5 or max( [len(x) for x in tracks] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( tracks )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + 0.5, tracks, rotation = rotation )

        return self.endPlot( plts, sorted_headers )
           
class RendererStackedBars(RendererTable, Plotter):
    """Stacked bars.

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def __call__( self, data, title ):

        if len(data) == 0: return results
        
        self.startPlot( )

        lines, legend = [], []

        nplotted = 0
        nskipped = 0
        
        legend, plts = [], []

        tracks = [ x[0] for x in data ]

        xvals = numpy.arange( (1.0 - self.mWidth) / 2., len(tracks) )
        sums = numpy.zeros( len(tracks), numpy.float )

        y = 0
        for header in sorted_headers:
            
            vals = numpy.zeros( len(tracks), numpy.float )
            x = 0
            for track, table in data:
                dd = dict(table)
                try: vals[x] = dd[header]
                except KeyError: pass
                x += 1

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals, vals, self.mWidth, 
                                  color = self.mColors[ y % len(self.mColors) ],
                                  bottom = sums )[0] )
            
            sums += vals
            y += 1

        if len( tracks ) > 5 or max( [len(x) for x in tracks] ) >= 8 : 
            rotation = "vertical"
            self.rescaleForVerticalLabels( tracks )
        else: 
            rotation = "horizontal"
        
        plt.xticks( xvals + self.mWidth / 2., 
                    tracks,
                    rotation = rotation )

        return self.endPlot( plts, sorted_headers )

class RendererPiePlot(RendererTable, Plotter):
    """Plot a pie chart
    """

    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        # used to enforce consistency of colors between plots
        self.mOrderedHeadersMap = {}
        self.mOrderedHeaders = []

        self.mFormat = "%i"

        try: self.mPieMinimumPercentage = float(kwargs["pie-min-percentage"])
        except KeyError: self.mPieMinPercentage = 0

    def __call__( self, data, title ):
        
        lines, legend = [], []

        blocks = ResultBlocks()

        labels = self.getLabels( data )
        paths = list(itertools.product( *labels[:-1] ))
        parts = labels[-1]
        for path in paths:
            work = self.getLeaf( data, path )
            if not work: continue

            self.startPlot()
            plts = []
            
            sorted_vals = [0] * len(parts)
            for x in range( len(parts) ):
                try:
                    sorted_vals[x] = work[parts[x]]
                except KeyError:
                    pass

            plts.append( plt.pie( sorted_vals, labels = parts ))
            blocks.extend( self.endPlot( plts ) )

        return blocks

class RendererMatrixPlot(RendererMatrix, PlotterMatrix):
    """Render a matrix as a matrix plot.

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        RendererMatrix.prepare( self, *args, **kwargs )
        PlotterMatrix.prepare( self, *args, **kwargs )
        self.mFormat = "%i"

    def render( self, data ):
        """render the data."""

        lines = []
        matrix, rows, columns = self.buildMatrix( data )
        return self.plotMatrix( matrix, rows, columns )

class RendererBoxPlot(Renderer, Plotter):        
    """Write a set of box plots.

    """
    
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def __call__(self, data, title ):

        self.startPlot()

        plts, legend = [], []
        nplotted = 0

        labels = self.getLabels( data )
        paths = list(itertools.product( *labels ))
        
        all_data = []
        for path in paths:
            work = self.getLeaf( data, path )
            if not work: continue
            assert isArray( work ), "work is of type '%s'" % work
            all_data.append( [ x for x in work if x != None ] )
            legend.append( "-".join(path) )

        plts.append( plt.boxplot( all_data ) )
        
        if len( legend ) > 5 or max( [len(x) for x in legend] ) >= 8 : 
            rotation = "vertical"
        else: 
            rotation = "horizontal"

        plt.xticks( [ x + 1 for x in range(0,len(legend)) ],
                    legend,
                    rotation = rotation,
                    fontsize="8" )

        return self.endPlot( plts, title = title )

class RendererCorrelation(Renderer):
    """Basic pairwise statistical analysis.

    Requires :class:`DataTypes.SingleColumnData`.
    """

    mRequiredType = type( SingleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )

    def addData( self, group, title, data ):
        self.mData[group].append( (title, data) )

    def getTestResults( self, data ):
        """perform pairwise statistical tests on data."""

        debug( "started pairwise statistical computations" )
        results = {}

        for x in range(len(data)):
            for y in range(x+1, len(data)):
                track1, xvals = data[x]
                track2, yvals = data[y]
                key = str(":".join( ("correl", track1, track2 ) ))
                result = self.getDataFromCache(key)
                if result == None:
                    if len(xvals) != len(yvals):
                        warn( "tracks returned vectors of unequal lengths: %s:%i and %s:%i" % \
                                  (track1,len(xvals),
                                   track2,len(yvals)) )
                    take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
                    xvals = [xvals[i] for i in take ]
                    yvals = [yvals[i] for i in take ]

                    result = Stats.doCorrelationTest( xvals, yvals )                    

                    try:
                        self.saveDataInCache( key, result )
                    except ValueError, msg:
                        continue

                results[(track1,track2)] = result

        debug( "finished pairwise statistical computations" )

        return results

    def render(self, data):
        lines = []
        if len(data) == 0: return lines

        tests = self.getTestResults( data )
        if len(tests) == 0: return lines

        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "track1","track2","%s" ' % '","'.join( Stats.CorrelationTest().getHeaders() ) )
        lines.append( '' )

        for x in range(len(data)):
            for y in range(x+1, len(data)):
                track1, xvals = data[x]
                track2, yvals = data[y]

                try:
                    result = tests[(track1,track2)]
                except KeyError:
                    continue
                lines.append( '   "%s","%s","%s"' % (track1, track2, '","'.join( [re.sub("[*]", "\*", i) for i in str(result).split("\t")]) ))

        lines.append( "" ) 

        return "\n".join(lines)

class RendererCorrelationPlot(RendererCorrelation, PlotterMatrix ):    
    """
    Plot of correlation structure in several variables.

    Options:

        *plot-value*
           value to plot ['coefficient', 'logP' ]

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererCorrelation.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        RendererCorrelation.prepare( self, *args, **kwargs )
        PlotterMatrix.prepare( self, *args, **kwargs )

    def render(self, data):
        """render the data.

        Data is a list of tuples of the from (track, data).
        """

        blocks = []

        if len(data) == 0: return blocks


        for x in range(len(data)):
            for y in range(x+1, len(data)):
                self.startPlot( data )
                plts = []
                track1, xvals = data[x]
                track2, yvals = data[y]
                take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
                xvals = [xvals[i] for i in take ]
                yvals = [yvals[i] for i in take ]
                plts.append( plt.scatter( xvals, yvals ) )
                blocks.append( self.endPlot( plts, legends = None, title="%s:%s" % (track1,track2) ) )
                
        return blocks

class RendererCorrelationMatrixPlot(RendererCorrelation, PlotterMatrix ):    
    """
    Plot of correlation structure in several variables.

    Options:

        *plot-value*
           value to plot ['coefficient', 'logP' ]

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererCorrelation.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def getCaption( self ):
        return """
        Plot of the correlation matrix. For each Pearson pairwise correlation between two variables,
        the plot shows the values of %s.
        """ % (self.mPlotValueName)
    
    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        PlotterMatrix.prepare( self, *args, **kwargs )

        self.mPlotValue = self.getCoefficient
        self.mPlotValueName = "the correlation coefficient"
        if "plot-value" in kwargs:
            v = kwargs["plot-value"]
            if v == "coefficient": 
                self.mPlotValue = self.getCoefficient
                self.mPlotValueName = "the correlation coefficient"
            elif v == "logP": 
                self.mPlotValue = self.getLogP
                self.mPlotValueName = "the logarithm of the P-Value. The minimum P-Value shown is 1e-10."
            else: raise ValueError("unknown option for 'plot-value': %s" % v )
            self.mPlotValueName = v

    def getCoefficient( self, r ):
        return r.mCoefficient

    def getLogP( self, r ):
        if r.mPValue > 1e-10: return math.log( r.mPValue )
        else: return math.log( 1e-10 )
    
    def render(self, data):
        """render the data.

        Data is a list of tuples of the from (track, data).
        """

        blocks = []

        tests = self.getTestResults( data )
        if len(tests) == 0: return blocks

        matrix = numpy.zeros( (len(data), len(data) ), numpy.float)

        headers = [ x[0] for x in data ]
        for x in range(len(data)):
            for y in range(x+1, len(data)):
                track1, xvals = data[x]
                track2, yvals = data[y]

                try:
                    result = tests[(track1,track2)]
                except KeyError:
                    continue

                v = self.mPlotValue( result )
                matrix[x,y] = matrix[y,x] = v

        blocks.extend(self.plotMatrix( matrix, headers, headers ) )

        return blocks

class RendererPairwiseStats(Renderer):
    """Basic pairwise statistical analysis.

    Requires :class:`DataTypes.MultipleColumnData`.
    """

    mRequiredType = type( MultipleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):

        Renderer.prepare( self, *args, **kwargs )

    def addData( self, group, title, data ):
        if len(data) < 2:
            raise ValueError("requiring at least two columns of data, received %i" % len(data))
        self.mData[group].append( (title, data) )

    def getTestResults( self, data ):
        """perform pairwise statistical tests on data."""

        debug( "started pairwise statistical computations" )
        results = {}

        for track, xx in data:
            headers, stats = xx
            if len(stats) == 0: continue

            for x in range(len(stats)):
                for y in range(x+1,len(stats)):
                    key = str(":".join( ("correl", track, headers[x], headers[y] ) ))
                    result = self.getDataFromCache(key)
                    if result == None:
                        xvals, yvals = stats[x], stats[y]
                        take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
                        xvals = [xvals[i] for i in take ]
                        yvals = [yvals[i] for i in take ]

                        try:
                            result = Stats.doCorrelationTest( xvals, yvals )
                        except ValueError, msg:
                            continue

                        self.saveDataInCache( key, (result,) )
                    else:
                        result = result[0]

                    results[(track,headers[x],headers[y])] = result

        debug( "finished pairwise statistical computations" )

        return results

    def render(self, data):
        lines = []
        if len(data) == 0: return lines

        tests = self.getTestResults( data )
        if len(tests) == 0: return lines

        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "track","var1","var2","%s" ' % '","'.join( Stats.CorrelationTest().getHeaders() ) )
        lines.append( '' )

        for track, xx in data:
            headers, stats = xx
            if len(stats) == 0: continue

            for x in range(len(stats)):
                for y in range(x+1,len(stats)):
                    try:
                        result = tests[(track,headers[x],headers[y])]
                    except KeyError:
                        continue
                    lines.append( '   "%s","%s","%s","%s"' % (track, headers[x], headers[y], '","'.join( [re.sub("[*]", "\*", i) for i in str(result).split("\t")]) ))

        lines.append( "" ) 

        return "\n".join(lines)

class RendererPairwiseStatsMatrixPlot(RendererPairwiseStats, PlotterMatrix ):    
    """
    Plot of correlation structure in several variables.

    Options:

        *plot-value*
           value to plot ['coefficient', 'logP' ]

    Requires :class:`DataTypes.MultipleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

    def getCaption( self ):
        return """
        Plot of the correlation matrix. For each Pearson pairwise correlation between two variables,
        the plot shows the values of %s.
        """ % (self.mPlotValueName)
    
    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        PlotterMatrix.prepare( self, *args, **kwargs )

        self.mPlotValue = self.getCoefficient
        self.mPlotValueName = "the correlation coefficient"
        if "plot-value" in kwargs:
            v = kwargs["plot-value"]
            if v == "coefficient": 
                self.mPlotValue = self.getCoefficient
                self.mPlotValueName = "the correlation coefficient"
            elif v == "logP": 
                self.mPlotValue = self.getLogP
                self.mPlotValueName = "the logarithm of the P-Value. The minimum P-Value shown is 1e-10."
            else: raise ValueError("unknown option for 'plot-value': %s" % v )
            self.mPlotValueName = v

    def getCoefficient( self, r ):
        return r.mCoefficient

    def getLogP( self, r ):
        if r.mPValue > 1e-10: return math.log( r.mPValue )
        else: return math.log( 1e-10 )
    
    def render(self, data):
        """render the data.

        Data is a list of tuples of the from (track, data).
        """

        blocks = []

        tests = self.getTestResults( data )
        if len(tests) == 0: return lines

        for track, vv in data:

            #if SUBSECTION_TOKEN:
            #    #result.extend( [track, SUBSECTION_TOKEN * len(track), "" ] )
            #    lines.extend( ["*%s*" % track, "" ] )

            headers, stats = vv
            if len(stats) == 0: continue

            matrix = numpy.zeros( (len( stats), len(stats) ), numpy.float)

            for x in range(len(stats)):
                for y in range(x+1,len(stats)):
                    try:
                        r = tests[(track,headers[x],headers[y])]
                    except KeyError:
                        continue
                    v = self.mPlotValue( r )
                    matrix[x,y] = matrix[y,x] = v

            blocks.extend(self.plotMatrix( matrix, headers, headers ) )

        return blocks

class RendererPairwiseStatsBarPlot(RendererPairwiseStats, Plotter ):    
    """
    Plot of correlation structure in several variables as a series
    of barplots.

    Options:

        *plot-value*
           value to plot ['coefficient', 'logP' ]

    Requires :class:`DataTypes.MultipleColumnData`.
    """
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def getCaption( self ):
        return """
        Plot of the correlation matrix. For each Pearson pairwise correlation between two variables,
        the plot shows the values of %s.
        """ % (self.mPlotValueName)
    
    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare( self, *args, **kwargs )

        self.mPlotValue = self.getCoefficient
        self.mPlotValueName = "the correlation coefficient"
        if "plot-value" in kwargs:
            v = kwargs["plot-value"]
            if v == "coefficient": 
                self.mPlotValue = self.getCoefficient
                self.mPlotValueName = "the correlation coefficient"
            elif v == "logP": 
                self.mPlotValue = self.getLogP
                self.mPlotValueName = "the logarithm of the P-Value. The minimum P-Value shown is 1e-10."
            else: raise ValueError("unknown option for 'plot-value': %s" % v )
            self.mPlotValueName = v

    def getCoefficient( self, r ):
        return r.mCoefficient

    def getLogP( self, r ):
        if r.mPValue > 1e-10: return math.log( r.mPValue )
        else: return math.log( 1e-10 )
    
    def render(self, data):
        """render the data.

        Data is a list of tuples of the from (track, data).
        """

        blocks = []

        tests = self.getTestResults( data )
        if len(tests) == 0: return blocks

        for track, vv in data:
#            if SUBSECTION_TOKEN:
#                lines.extend( [track, SUBSECTION_TOKEN * len(track), "" ] )

            headers, stats = vv
            
            if len(stats) == 0: continue

            matrix = numpy.zeros( (len( stats), len(stats) ), numpy.float)


            for x in range(len(stats)):
                for y in range(x+1,len(stats)):
                    try:
                        r = tests[(track,x,y)]
                    except IndexError:
                        continue
                    v = self.mPlotValue( r )
                    matrix[x,y] = matrix[y,x] = v

            # plot interleaved bars for each track
            self.startPlot( data )
            plts = []
            width = 1.0 / (len(stats) + 1)
            offset = width / 2.0
            xvals = arange( 0, len(stats) )

            y = 0
            for x in range(len(stats)):

                plts.append( plt.bar( xvals + offset, matrix[:,y], 
                                      width,
                                      color = self.mColors[ y % len(self.mColors) ] )[0] )


                offset += width
                y += 1

            if len( tracks ) > 5 or max( [len(x) for x in headers] ) >= 8 : 
                rotation = "vertical"
                self.rescaleForVerticalLabels( headers )
            else: 
                rotation = "horizontal"
        
            plt.xticks( xvals + 0.5, headers, rotation = rotation )

            blocks.extend( self.endPlot( plts, headers) )

        return blocks

class RendererScatterPlot(Renderer, Plotter):
    """Scatter plot.

    Requires :class:`DataTypes.MultipleColumnData`.
    """

    mRequiredType = type( MultipleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def render(self, data):
        self.startPlot( data )

        nplotted = 0

        plts, legend = [], []

        for track, vv in data:

            headers, values = vv
            if len(values) == 0: continue

            marker = self.mMarkers[nplotted % len(self.mMarkers)]
            color = self.mColors[nplotted % len(self.mColors)]
            xvals, yvals = values
            if len(xvals) == 0 or len(yvals) == 0: continue
            plts.append(plt.scatter( xvals,
                                     yvals,
                                     marker = marker,
                                     c = color) )
            legend.append( track )

            nplotted += 1
            
        return self.endPlot( plts, legend )

class RendererScatterPlotWithColor( Renderer, Plotter ):
    """Scatter plot with individual colors for each dot.

    Requires :class:`DataTypes.MultipleColumnData`.
    and interpretes it as (x,y,color).

    This class adds the following options to the :term:`render` directive:

       :term:`colorbar-format`: numerical format for the colorbar.

       :term:`palette`: numerical format for the colorbar.

       :term:`zrange`: restrict plot a part of the z-axis.
    
    """

    mRequiredType = type( MultipleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )

        try: self.mBarFormat = kwargs["colorbar-format"]
        except KeyError: self.mBarFormat = "%1.1f"

        try: self.mPalette = kwargs["palette"]
        except KeyError: self.mPalette = "jet"

        try: self.mZRange = map(float, kwargs["zrange"].split(",") )
        except KeyError: self.mZRange = None

        self.mReversePalette = "reverse-palette" in kwargs

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def render(self, data):

        blocks = []
        nplotted = 0

        if self.mPalette:
            if self.mReversePalette:
                color_scheme = eval( "plt.cm.%s_r" % self.mPalette)                    
            else:
                color_scheme = eval( "plt.cm.%s" % self.mPalette)
        else:
            color_scheme = None

        for track, vv in data:

            self.startPlot( data )
            plts, legend = [], []

            headers, values = vv
            if len(values) == 0: continue

            xvals, yvals, colors = values
            if len(xvals) == 0 or len(yvals) == 0 or len(colors) == 0: continue

            if self.mZRange:
                vmin, vmax = self.mZRange
                colors[ colors < vmin ] = vmin
                colors[ colors > vmax ] = vmax
            else:
                vmin, vmax = None, None

            plts.append(plt.scatter( xvals,
                                     yvals,
                                     c = colors,
                                     vmax = vmax,
                                     vmin = vmin ) )
            
            plt.colorbar( format = self.mBarFormat)        
            nplotted += 1

            blocks.extend( self.endPlot( plts, title = track ) )

        return blocks

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

            self.startPlot( data )
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

class RendererGroupedTable(Renderer):    
    """A table with grouped data.

    Requires :class:`DataTypes.MultipleColumns`.
    """

    mRequiredType = type( MultipleColumns( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
        self.mFormat = "%i"

    def addData( self, group, title, data ):
        self.mData[group].append( (title, data ) )

    def getHeaders( self ):
        """return a list of headers and a mapping of header to column."""
        # preserve the order of columns
        headers = {}
        sorted_headers = []
        for group, data in self.mData.iteritems():
            for track, d in data:
                columns, data = d
                for h in columns:
                    if h not in headers: 
                        headers[h] = len(headers)
                        sorted_headers.append(h)

        return sorted_headers, headers

    def commit(self): 
        
        debug( "%s: rendering data started" % (self.mTracker,) )
        
        result = []
        
        sorted_headers, headers = self.getHeaders()

        result.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        result.append( '   :header: "group", "track","%s" ' % '","'.join( sorted_headers ) )
        result.append( '')

        def toValue( dd, x ):
            if dd[x] == None:
                return "na"
            else:
                return str(dd[x])

        for group, data in self.mData.iteritems():
            g = "*%s*" % group
            for track, d in data:
                columns, data = d
                # tranpose to row-oriented format
                for row in zip( *data ):
                    dd = dict( zip( columns, row) )
                    result.append( '   "%s","*%s*","%s"' % ( g,track, '","'.join( [toValue( dd, x) for x in sorted_headers] )))
                    g = ""

        return [ ResultBlock( "\n".join(result) ), ]

        

