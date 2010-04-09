import os, sys, re, shelve, traceback, cPickle, types, itertools

# so that arange is available in eval
import numpy
import numpy.ma
from numpy import *
from math import *

import Stats
import Histogram
import collections
import CorrespondenceAnalysis

from SphinxReport.ResultBlock import ResultBlock, EmptyResultBlock, ResultBlocks
from SphinxReport.odict import OrderedDict as odict
from SphinxReport.DataTree import DataTree, path2str, tree2table
from SphinxReport.Component import *
from SphinxReport import Utils

from docutils.parsers.rst import directives

class Renderer(Component):
    """Base class of renderers that render data into restructured text.

    The subclasses define how to render the data by overloading the
    :meth:`render` method.

    When called, a Renderer and its subclasses will return blocks of
    restructured text. Images are automatically collected from matplotlib
    and inserted at place-holders.

    This class adds the following options to the :term:`report` directive.

       :term:`groupby`: group data by :term:`track` or :term:`slice`.
    """
    # plugin fields
    capabilities = ["render"]

    options = ( ('format', directives.unchanged), )

    # required levels in DataTree
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

class TableBase( Renderer ):
    '''base classes for tables and matrices.'''

    options = Renderer.options +\
        ( ('force', directives.unchanged), )
    
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

class Table( TableBase ):
    '''a basic table. 

    Values are either text or converted to text.

    If the has more rows than :attr:`max_rows` or more columns
    than :attr:`max_cols`, a placeholder will be inserted pointing
    towards a file.
    '''
    options = TableBase.options +\
        ( ('transpose', directives.unchanged), )

    nlevels = 2

    transpose = False

    def __init__( self, *args, **kwargs ):
        TableBase.__init__(self, *args, **kwargs )

        self.transpose = "transpose" in kwargs

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
            raise ValueError("mal-formatted data - Table expected three level dictionary, got %s." % str(data) )

        return sorted_headers, column_headers


    def buildTable( self, data ):
        """build table from data.

        If there is more than one column, additional subrows
        are added for each.

        If each cell within a row is a list or tuple, multiple
        subrows will be created as well.

        returns matrix, row_headers, col_headers
        """

        return tree2table( data, self.transpose )

    def __call__(self, data, path):


        matrix, row_headers, col_headers = self.buildTable( data )
        title = "/".join(path)

        if matrix == None: 
            return ResultBlocks( ResultBlock( "\n".join(lines), title = title) )

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

class Glossary( Table ):
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

class Matrix(TableBase):    
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

    options = TableBase.options +\
        ( ('transform-matrix', directives.unchanged), )

    def __init__(self, *args, **kwargs):
        TableBase.__init__(self, *args, **kwargs )

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

class Debug( Renderer ):
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
        
    
    

