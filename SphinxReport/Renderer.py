import os, sys, re, shelve, traceback, cPickle, types, itertools

from Plotter import *
from Tracker import *

from math import *

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers
import matplotlib.transforms

import bsddb.db

import numpy
import numpy.ma
# so that arange is available in eval
from numpy import *

import sqlalchemy

import Stats
import Histogram
import collections
import CorrespondenceAnalysis

from SphinxReport.ResultBlock import ResultBlock, EmptyResultBlock, ResultBlocks
from SphinxReport.odict import OrderedDict as odict
from SphinxReport.DataTree import DataTree, path2str, tree2table
from SphinxReport.Reporter import *
from SphinxReport import Utils

def buildException( stage ):
    '''build an exception text element.
    
    It uses the last exception.
    '''
        
    if sphinxreport_show_errors:
        EXCEPTION_TEMPLATE = '''
.. error:: %(exception_name)s

   * stage: %(stage)s
   * exception: %(exception_name)s
   * message: %(exception_value)s
   * traceback: 

%(exception_stack)s
'''

        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        lines = traceback.format_tb( exceptionTraceback )
        # remove all the ones relate to Dispatcher.py
        xlines = filter( lambda x: not re.search( "Dispatcher.py", x ), lines )
        # if nothing left, use the full traceback
        if len(xlines) > 0: lines = xlines
        # add prefix of 6 spaces
        prefix = "\n" + " " * 6
        exception_stack  = prefix + prefix.join( "".join(lines).split("\n") )
        if exceptionType.__module__ == "exceptions":
            exception_name   = exceptionType.__name__
        else:
            exception_name   = exceptionType.__module__ + '.' + exceptionType.__name__

        exception_value  = str(exceptionValue)

        return ResultBlocks( 
            ResultBlocks( 
                ResultBlock( EXCEPTION_TEMPLATE % locals(), 
                         title = "" ) ) )
    else:
        return ResultBlocks()

class Renderer(Reporter):
    """Base class of renderers that render data into restructured text.

    The subclasses define how to render the data by overloading the
    :meth:`render` method.

    When called, a Renderer and its subclasses will return blocks of
    restructured text. Images are automatically collected from matplotlib
    and inserted at place-holders.

    This class adds the following options to the :term:`report` directive.

       :term:`groupby`: group data by :term:`track` or :term:`slice`.
    """

    # required levels in nested dictionary
    nlevels = None

    # default number format
    format = "%i"

    def __init__(self, *args, **kwargs ):
        """create an Renderer object using an instance of 
        a :class:`Tracker.Tracker`.
        """

        debug("%s: starting renderer '%s'"% (id(self), str(self)))

        try: self.format = kwargs["format"]
        except KeyError: pass

    def __call__(self):
        return None

    def __call__(self, data, path ):
        '''iterate over leaves/branches in data structure.

        This method will call the :meth:`render` method for 
        each leaf/branch at level :attr:`nlevels`.
        '''
        if self.nlevels == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        result = ResultBlocks( title = path2str(path) )

        labels = data.getPaths()
        if len(labels) < self.nlevels:
            warn( "at %s: expected at least %i levels - got %i: %s" %\
                      (str(path), self.nlevels, len(labels), str(labels)) )
            result.append( EmptyResultBlock( title = path2str(path) ) )
            return result

        paths = list(itertools.product( *labels[:-self.nlevels] ))

        for p in paths:
            work = data.getLeaf( p )
            if not work: continue
            try:
                result.extend( self.render( DataTree(work), path + p ) )
            except:
                warn("exeception raised in rendering for path: %s" % str(path+p))
                raise 
            
        return result

class RendererTableBase( Renderer ):
    '''base classes for tables and matrices.'''
    
    max_rows = 50
    max_cols = 20

    def __init__( self, *args, **kwargs ):
        Renderer.__init__(self, *args, **kwargs )
        self.force = "force" in kwargs            

    def asFile( self, matrix, row_headers, col_headers, title ):
        '''save the table as HTML file.

        Multiple files of the same Renderer/Tracker combination are distinguished 
        by the title.
        '''

        debug("%s: saving %i x %i table as file'"% (id(self), 
                                                    len(row_headers), 
                                                    len(col_headers)))
        lines = []
        lines.append("`%i x %i table <#$html %s$#>`_" %\
                     (len(row_headers), len(col_headers),
                      title) )

        r = ResultBlock( "\n".join(lines), title = title)
        # create an html table
        data = ["<table>"]
        data.append( "<tr><th></th><th>%s</th></tr>" % "</th><th>".join( col_headers) )
        for h, row in zip( row_headers, matrix):
            data.append( "<tr><th>%s</th><td>%s</td></tr>" % (h, "</td><td>".join(row) ))
        data.append( "</table>\n" )
        r.html = "\n".join( data )

        return ResultBlocks( r )

    def removeRedundantCells( self, matrix ):
        '''remove cells in a matrix that are the same as
        the ones above the top.'''
        
        nrows = len(matrix)
        for x in xrange(nrows-1, 0, -1):
            row = matrix[x]
            for y in range(len(row)):
                if row[y] == matrix[x-1][y]:
                    row[y] = ""
        return matrix

class RendererTable( RendererTableBase ):
    '''a basic table. 

    Values are either text or converted to text.

    If the has more rows than :attr:`max_rows` or more columns
    than :attr:`max_cols`, a placeholder will be inserted pointing
    towards a file.
    '''

    nlevels = 2

    def __init__( self, *args, **kwargs ):
        RendererTableBase.__init__(self, *args, **kwargs )
        self.mTranspose = "transpose" in kwargs
        self.mFormat = kwargs.get( "format", "").split(",")

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

        If there is more than one column, additional subrows
        are added for each.

        If each cell within a row is a list or tuple, multiple
        subrows will be created as well.

        returns matrix, row_headers, col_headers
        """

        return tree2table( data, self.mTranspose )

    def __call__(self, data, path):


        matrix, row_headers, col_headers = self.buildTable( data )
        title = "/".join(path)

        if matrix == None: 
            return ResultBlocks( ResultBlock( "\n".join(lines), title = title) )

        if "grouped" in self.mFormat:
            matrix = self.removeRedundantCells( matrix )

        # do not output large matrices as rst files
        if not self.force and (len(row_headers) > self.max_rows or len(col_headers) > self.max_cols):
            return self.asFile( matrix, row_headers, col_headers, title )

        lines = []
        lines.append( ".. csv-table:: %s" % title )
        lines.append( '   :header: "", "%s" ' % '","'.join( col_headers ) )
        lines.append( '' )

        for header, line in zip( row_headers, matrix ):
            lines.append( '   "%s","%s"' % (header, '","'.join( line ) ) )

        lines.append( "") 
        
        return ResultBlocks( ResultBlock( "\n".join(lines), title = title) )

class RendererGlossary( RendererTable ):
    """output a table in the form of a glossary."""

    def __call__(self, data, path ):

        lines = []
        matrix, row_headers, col_headers = self.buildTable( data )

        if matrix == None: return lines

        title = "/".join(path)

        lines.append( ".. glossary::" )

        lines.append( "") 

        for header, line in zip( row_headers, matrix ):
            txt = "\n".join( line )
            txt = "\n      ".join( [ x.strip() for x in txt.split("\n" ) ] )
            lines.append( '   %s\n      %s' % ( header, txt ) )

        lines.append( "") 

        return ResultBlocks( "\n".join(lines), title = title )

class RendererMatrix(RendererTableBase):    
    """A table with numerical columns.

    It implements column-wise and row-wise transformations.

    This class adds the following options to the :term:`report` directive.

        :term:`transform-matrix`: apply a matrix transform. Possible choices are:

           * *correspondence-analysis*: use correspondence analysis to permute rows/columns 
           * *normalized-column-total*: normalize by column total
           * *normalized-column-max*: normalize by column maximum
           * *normalized-row-total*: normalize by row total
           * *normalized-row-max*: normalize by row maximum
           * *normalized-total*: normalize over whole matrix
           * *normalized-max*: normalize over whole matrix
           * *sort* : sort matrix rows and columns alphanumerically.
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
        RendererTableBase.__init__(self, *args, **kwargs )

        self.mMapKeywordToTransform = {
            "correspondence-analysis": self.transformCorrespondenceAnalysis,
            "transpose": self.transformTranspose,
            "normalized-row-total" : self.transformNormalizeRowTotal,
            "normalized-row-max" : self.transformNormalizeRowMax,
            "normalized-col-total" : self.transformNormalizeColumnTotal,
            "normalized-col-max" : self.transformNormalizeColumnMax ,
            "normalized-total" : self.transformNormalizeTotal,
            "normalized-max" : self.transformNormalizeMax,
            "symmetric-max" : self.transformSymmetricMax,
            "symmetric-min" : self.transformSymmetricMin,
            "symmetric-avg" : self.transformSymmetricAverage,
            "symmetric-sum" : self.transformSymmetricSum,
            "filter-by-rows" : self.transformFilterByRows,
            "filter-by-cols" : self.transformFilterByColumns,
            "square" : self.transformSquare,
            "add-row-total" : self.transformAddRowTotal,
            "add-column-total" : self.transformAddColumnTotal,
            "sort" : self.transformSort,
        }
        
        self.mConverters = []        
        if "transform-matrix" in kwargs:
            for kw in [x.strip() for x in kwargs["transform-matrix"].split(",")]:
                if kw.startswith( "normalized" ): self.format = "%6.4f"
                try:
                    self.mConverters.append( self.mMapKeywordToTransform[ kw ] )
                except KeyError:
                    raise ValueError("unknown matrix transformation %s" % kw )


    def transformAddRowTotal( self, matrix, row_headers, col_headers ):
        '''add row total to the matrix.'''
        nrows, ncols = matrix.shape

        totals = numpy.zeros( nrows )
        for x in range(nrows): totals[x] = sum(matrix[x,:])
        col_headers.append( "total" )
        totals.shape=(nrows,1)
        return numpy.hstack( numpy.hsplit(matrix,ncols) + [totals,] ), row_headers, col_headers

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

    def transformSort( self, matrix, row_headers, col_headers ):
        """apply correspondence analysis to a matrix.
        """

        map_row_new2old = [x[0] for x in sorted(enumerate( row_headers ), key=lambda x: x[1])]
        map_col_new2old = [x[0] for x in sorted(enumerate( col_headers ), key=lambda x: x[1])]

        matrix, row_headers, col_headers =  CorrespondenceAnalysis.GetPermutatedMatrix( matrix,
                                                                                        map_row_new2old,
                                                                                        map_col_new2old,
                                                                                        row_headers = row_headers,
                                                                                        col_headers = col_headers)


        return matrix, row_headers, col_headers

    def transformSymmetricMax( self, matrix, rows, cols ):
        """symmetrize a matrix.

        returns the normalized matrix.
        """
        if len(rows) != len(cols):
            raise ValueError( "matrix not square - can not be symmetrized" )
        
        for x in xrange(len(rows)):
            for y in xrange(x+1,len(cols)):
                matrix[x,y] = matrix[y,x] = max(matrix[x,y], matrix[y,x])

        return matrix, rows, cols

    def transformSymmetricMin( self, matrix, rows, cols ):
        """symmetrize a matrix.

        returns the normalized matrix.
        """
        if len(rows) != len(cols):
            raise ValueError( "matrix not square - can not be symmetrized" )
        
        for x in xrange(len(rows)):
            for y in xrange(x+1,len(cols)):
                matrix[x,y] = matrix[y,x] = min(matrix[x,y], matrix[y,x])

        return matrix, rows, cols

    def transformSymmetricSum( self, matrix, rows, cols ):
        """symmetrize a matrix.

        returns the normalized matrix.
        """
        if len(rows) != len(cols):
            raise ValueError( "matrix not square - can not be symmetrized" )
        
        for x in xrange(len(rows)):
            for y in xrange(x+1,len(cols)):
                matrix[x,y] = matrix[y,x] = sum(matrix[x,y], matrix[y,x])

        return matrix, rows, cols

    def transformSymmetricAverage( self, matrix, rows, cols ):
        """symmetrize a matrix.

        returns the normalized matrix.
        """
        if len(rows) != len(cols):
            raise ValueError( "matrix not square - can not be symmetrized" )
        
        for x in xrange(len(rows)):
            for y in xrange(x+1,len(cols)):
                matrix[x,y] = matrix[y,x] = sum(matrix[x,y], matrix[y,x]) / 2

        return matrix, rows, cols

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
            m = sum(matrix[x,:])
            if m != 0:
                for y in range(ncols):
                    matrix[x,y] /= m
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

    def buildMatrix( self, work, 
                     missing_value = 0, 
                     apply_transformations = True,
                     take = None,
                     dtype = numpy.float ):
        """build a matrix from work, a two-level nested dictionary.

        If *take* is given, then the matrix will be built from
        level 3, taking *take* from the deepest level only.

        This method will also apply conversions if apply_transformations
        is set.
        """

        labels = work.getPaths()
        levels = len(labels)
        if take:
            if levels != 3: raise ValueError( "expected three labels" )
            if take not in labels[-1]: raise ValueError( "no data on `%s`" % take )
            take_f = lambda row,column: work[row][column][take]
        else:
            if levels != 2: raise ValueError( "expected two levels" )
            take_f = lambda row,column: work[row][column]

        rows, columns = labels[:2]

        self.debug("creating matrix")
        matrix = numpy.array( [missing_value] * (len(rows) * len(columns) ), dtype )
        matrix.shape = (len(rows), len(columns) )
        self.debug("constructing matrix")
        for x,row in enumerate(rows):
            for y, column in enumerate(columns):
                # deal with empty values from DataTree
                try:
                    matrix[x,y] = take_f( row, column )
                except KeyError:
                    pass
                except ValueError:
                    raise ValueError( "malformatted data: expected scalar, got '%s'" % str(work[row][column]) )
                except TypeError:
                    raise TypeError( "malformatted data: expected scalar, got '%s'" % str(work[row][column]) )
        
        
        if self.mConverters and apply_transformations:
            for converter in self.mConverters: 
                self.debug("applying converter %s" % converter)
                matrix, rows, columns = converter(matrix, rows, columns)

        # convert rows/columns to str (might be None)
        rows = [ str(x) for x in rows ]
        columns = [ str(x) for x in columns ]

        return matrix, rows, columns

    def render( self, work, path ):
        """render the data.
        """

        results = ResultBlocks( title = path )

        matrix, rows, columns = self.buildMatrix( work )
        title = "/".join(path)

        if len(rows) == 0:
            return ResultBlocks( ResultBlock( "\n".join(lines), title = title) )

        # do not output large matrices as rst files
        if not self.force and (len(rows) > self.max_rows or len(columns) > self.max_cols):
            return self.asFile( [ [ self.format % x for x in r ] for r in matrix ], 
                                rows, 
                                columns, 
                                title )

        lines = []
        lines.append( ".. csv-table:: %s" % title )
        lines.append( '   :header: "track","%s" ' % '","'.join( columns ) )
        lines.append( '')
        for x in range(len(rows)):
            lines.append( '   "%s","%s"' % (rows[x], '","'.join( [ self.format % x for x in matrix[x,:] ] ) ) )
        lines.append( "") 
        if not path: subtitle = ""
        else: subtitle = "/".join(path)

        results.append( ResultBlock( "\n".join(lines), title = subtitle ) )

        return results

class RendererLinePlot( Renderer, Plotter ):
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
                    warn("could not plot %s - coords is not a dict: %s" % (label, str(coords) ))
                    continue
                
                if len(keys) <= 1:
                    warn("could not plot %s: not enough columns: %s" % (label, str(coords) ))
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
        
class RendererHistogramPlot(RendererLinePlot):        
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

    def __init__(self, *args, **kwargs):
        RendererLinePlot.__init__(self,*args, **kwargs)

        try: self.error = kwargs["error"]
        except KeyError: pass

    def initPlot( self, fig, work, path ):
        RendererLinePlot.initPlot( self, fig, work, path )
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

        RendererLinePlot.finishPlot(self, fig, work, path)
        # there is a problem with legends
        # even though len(plts) == len(legend)
        # matplotlib thinks there are more. 
        # In fact, it thinks it is len(plts) = len(legend) * len(xvals)
        self.legend = None
                        
class RendererHistogramGradientPlot(RendererLinePlot):        
    '''create a series of coloured bars from histogram data.

    This :class:`Renderer` requires at least three levels:

    line / data / coords.
    '''
    nlevels = 3

    def __init__(self, *args, **kwargs):
        RendererLinePlot.__init__(self, *args, **kwargs )

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

        RendererLinePlot.initPlot( self, fig, work, path )

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

        if self.mZRange:
            self.ymin, self.ymax = self.mZRange

    def addData( self, line, label, xlabel, ylabel,
                 xvals, yvals, nplotted ):

        if self.mZRange:
            vmin, vmax = self.mZRange
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
        ax.set_xticks( xrange( 0, len(self.xvals), increment ) ) 
        ax.set_xticklabels( [self.xvals[x] for x in xrange( 0, len(self.xvals), increment ) ] )

        RendererLinePlot.finishPlot(self, fig, work, path)
        self.legend = None

        # add colorbar on the right
        plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
        cax = plt.axes([0.85, 0.1, 0.075, 0.8])
        plt.colorbar(cax=cax, format=self.mBarFormat )

class RendererBarPlot( RendererMatrix, Plotter):
    '''A bar plot.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    '''

    # column to use for error bars
    error = None

    # column to use for labels
    label = None

    label_offset_x = 10
    label_offset_y = 5

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        try: self.error = kwargs["error"]
        except KeyError: pass

        try: self.label = kwargs["label"]
        except KeyError: pass

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
            labels = work.getPaths()
            label = list(set(labels[-1]).difference( set(("error", "label")) ))[0]
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

        xvals = numpy.arange( 0, len(self.rows) )

        # plot by row
        y, error = 0, None
        for column,header in enumerate(self.columns):
            
            vals = self.matrix[:,column]
            if self.error: error = self.error_matrix[:,column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0

            plts.append( plt.bar( xvals, 
                                  vals,
                                  self.mWidth, 
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

class RendererInterleavedBarPlot(RendererBarPlot):
    """A plot with interleaved bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """

    def __init__(self, *args, **kwargs):
        RendererBarPlot.__init__(self, *args, **kwargs )

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
            if isnan(vals[0]) or isinf( vals[0] ): 
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
           
class RendererStackedBarPlot(RendererBarPlot ):
    """A plot with stacked bars.

    This :class:`Renderer` requires two levels:
    rows[dict] / cols[dict]
    """
    def __init__(self, *args, **kwargs):
        RendererBarPlot.__init__(self, *args, **kwargs )

    def render( self, work, path ):

        self.buildMatrices( work)
        
        self.startPlot( )

        plts = []

        xvals = numpy.arange( (1.0 - self.mWidth) / 2., len(self.rows) )
        sums = numpy.zeros( len(self.rows), numpy.float )

        y, error = 0, None
        for column,header in enumerate(self.columns):

            vals = self.matrix[:,column]            
            if self.error: error = self.error_matrix[:,column]

            # patch for wrong ylim. matplotlib will set the yrange
            # inappropriately, if the first value is None or nan
            # set to 0. Nan values elsewhere are fine.
            if isnan(vals[0]) or isinf( vals[0] ): 
                vals[0] = 0
                
            plts.append( plt.bar( xvals, 
                                  vals, 
                                  self.mWidth, 
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
        
        plt.xticks( xvals + self.mWidth / 2., 
                    self.rows,
                    rotation = rotation )

        return self.endPlot( plts, self.columns, path )

class RendererPiePlot(Renderer, Plotter):
    """A pie chart.

    This :class:`Renderer` requires one level:
    entries[dict] 
    """
    nlevels = 1
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

        try: self.mPieMinimumPercentage = float(kwargs["pie-min-percentage"])
        except KeyError: self.mPieMinPercentage = 0

        self.sorted_headers = odict()

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

    def render( self, work, path ):
        """render the data."""

        self.debug("building matrix started")
        matrix, rows, columns = self.buildMatrix( work )
        self.debug("building matrix finished")
        return self.plot( matrix, rows, columns, path )

class RendererHintonPlot(RendererMatrix, PlotterHinton):
    """Render a matrix as a hinton plot.
    """

    def __init__(self, *args, **kwargs):
        RendererMatrix.__init__(self, *args, **kwargs )
        PlotterMatrix.__init__(self, *args, **kwargs )

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
                assert Utils.isArray( values ), "work is of type '%s'" % values
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
            xvals, yvals = Stats.filterNone( coords.values()[:2])

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

    This class adds the following options to the :term:`report` directive:

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
            zvals = numpy.array( zvals )
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

class RendererDebug( Renderer ):
    '''a simple renderer, returning the type of data and the number of items at each path.'''

    # only look at leaves
    nlevels = 1

    def render( self, work, path ):

        # initiate output structure
        results = ResultBlocks( title = path )

        # iterate over all items at leaf
        for key in work:

            t = type(work[key])
            try:
                l = "%i" % len(work[key])
            except AttributeError:
                l = "na"
            except TypeError:
                l = "na"
                
            # add a result block.
            results.append( ResultBlock( "debug: path=%s, key=%s, type=%s, len=%s" % \
                                             ( path2str(path),
                                               str(key),
                                               t, l), title = "") )

        return results
        
    
    

