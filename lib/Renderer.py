import os, sys, re, shelve, traceback

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
from logging import warn, log, debug, info
import logging

from DataTypes import *

# Some renderers will build several objects.
# Use these two rst levels to separate individual
# entries. Set to None if not separation.
SECTION_TOKEN = "@"
SUBSECTION_TOKEN = "^"

VERBOSE=True

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( "sphinxreport.log", "a" ) )

# for cachedir
if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

class Renderer:
    """Base class of renderes that render data into restructured text.

    The subclasses define how to render the data by overloading the
    :meth:`render` method.

    If a subclass creates images with matplotlib, then these are automatically
    collected from matplotlib and saved to disc by the :term:`render` directive.
    In this case, the :meth:`render` method return place-holders::
    
       return [ "## Figure 1 ##", "## Figure 2 ##" ]``.

    The base class implements querying the :attr:`mTracker` for tracks and 
    slices and then asking the tracker for data grouped by tracks or slices.

    This class adds the following options to the :term:`render` directive.

       :term:`groupby`: group data by :term:`track` or :term:`slice`.
        
    """
    mRequiredType = None

    def __init__(self, tracker ):
        """create an Renderer object using an instance of 
        a :class:`Tracker.Tracker`.
        """

        debug("starting renderer '%s' with tracker '%s'" % (str(self), str(tracker) ) )

        self.mTracker = tracker
        global cachedir
        try:
            if not os.path.exists(cachedir): os.mkdir(cachedir)
        except (NameError, TypeError):
            cachedir = None

        if cachedir:
            self.mCacheFile = os.path.join( cachedir, tracker.__class__.__name__ )
            self._cache = shelve.open(self.mCacheFile,"c", writeback = False)
            debug( "using cache %s" % self.mCacheFile )
            debug( "keys in cache: %s" % (str(self._cache.keys() ) ))
        else:
            self.mCacheFile = None
            self._cache = None
            debug( "not using cache" )

    def __del__(self):
        
        if self._cache != None: 
            return
            debug("closing cache %s" % self.mCacheFile )
            debug( "keys in cache %s" % (str(self._cache.keys() ) ))
            self._cache.close()
            self._cache = None

    def getCaption( self ):
        """return a caption string."""
        return self.__doc__

    def prepare(self, *args, **kwargs ): 

        try: self.mLayout = kwargs["layout"]
        except KeyError: self.mLayout = "column"

        try: self.mGroupBy = kwargs["groupby"]
        except KeyError: self.mGroupBy = "slice"

        try: self.mTracks = [ x.strip() for x in kwargs["tracks"].split(",")]
        except KeyError: self.mTracks = None

        try: 
            self.mSlices = [ x.strip() for x in kwargs["slices"].split(",")]
            if len(self.mSlices) == 1: self.mSlices = self.mSlices[0]
        except KeyError: self.mSlices = None

        self.mData = collections.defaultdict( list )

    def normalize_max( self, data ):
        """normalize a data vector by maximum.
        """
        if data == None or len(data) == 0: return data
        m = max(data)
        data = data.astype( numpy.float )
        # numpy does not throw at division by zero, but sets values to Inf
        return data / m

    def normalize_total( self, data ):
        """normalize a data vector by the total"""
        if data == None or len(data) == 0: return data
        try:
            m = sum(data)
        except TypeError:
            return data
        data = data.astype( numpy.float )
        # numpy does not throw at division by zero, but sets values to Inf
        return data / m

    def getDataFromCache( self, key ):

        result = None
        if self._cache != None:
            try:
                if key in self._cache: 
                    result = self._cache[key]
                    debug( "retrieved data for key '%s' from cache: %i" % (key, len(result)) )
                else:
                    result = None
                    debug( "key '%s' not found in cache" % key )

            except (bsddb.db.DBPageNotFoundError, bsddb.db.DBAccessError), msg:
                self.warn( "could not get key '%s' in '%s': msg=%s" % (key,self.mCacheFile, msg) )

        return result

    def saveDataInCache( self, key, data ):

        if self._cache != None:
            try:
                self._cache[key] = data
                debug( "saved data for key '%s' in cache" % key )
            except (bsddb.db.DBPageNotFoundError,bsddb.db.DBAccessError), msg:
                warn( "could not save key '%s' from '%s': msg=%s" % (key,self.mCacheFile,msg) )
            # The following sync call is absolutely necessary when using 
            # the multiprocessing library (python 2.6.1). Otherwise the cache is emptied somewhere 
            # before the final call to close(). Even necessary, if writeback = False
            self._cache.sync()

    def getData( self, track, slice):
        """get data for track and slice. Save data in persistent cache for further use."""

        key = ":".join( (track.encode(), str(slice)) )

        result = self.getDataFromCache( key )

        if result == None:
            try:
                result = self.mTracker( track, slice )
                debug( "collected data for key '%s': %i" % (key, len(result)) )
            except Exception, msg:
                warn( "exception for tracker '%s', track '%s' and slice '%s': msg=%s" % (str(self.mTracker), track, slice, msg) )
                if VERBOSE: warn( traceback.format_exc() )
                result = []
            
        self.saveDataInCache( key, result )

        debug( "collected data for tracker '%s', track '%s' and slice '%s': %i" % (str(self.mTracker), track, slice, len(result)) )

        ## check if data is correctly formatted
        if result and self.mRequiredType != None:
            if type(result) != self.mRequiredType:
                warn( "tracker %s returned invalid type for %s: required=%s, returned=%s" % (str(self.mTracker), str(self), str(self.mRequiredType), type(result) ) )
                return []

        return result

    def collectData( self ):

        if self.mTracks == None:
            tracks = self.mTracker.getTracks()
        else:
            tracks = self.mTracks

        if len(tracks) == 0: 
            debug( "%s: no tracks found - no output" % self.mTracker )
            return

        slices = self.mTracker.getSlices( subset = self.mSlices )
        if type(slices) in types.StringTypes: slices=[slices,]
        if len(slices) == 0: slices=[None,]

        debug( "%s: collecting data started for %i pairs, %i tracks: %s, %i slices: %s" % (self.mTracker, len(tracks) * len(slices), 
                                                                                           len(tracks), str(tracks),
                                                                                           len(slices), str(slices) ) )

        # group by tracks
        if self.mGroupBy == "track":
            for track in tracks:
                for slice in slices:
                    data = self.getData( track, slice )
                    if len(data) == 0: continue
                    self.addData( track, slice, data )
        # group by slices
        elif self.mGroupBy == "slice":
            for slice in slices:
                for track in tracks:
                    data = self.getData( track, slice )
                    if len(data) == 0: continue
                    self.addData( slice, track, data )
        else:
            for slice in slices:
                for track in tracks:
                    data = self.getData( track, slice )
                    if len(data) == 0: continue
                    self.addData( "all", track + "_" + slice, data )

        debug( "%s: collecting data finished for %i pairs, %i tracks, %i slices" % (self.mTracker, len(tracks) * len(slices), len(tracks), len(slices)) )

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def commit(self): 
        
        debug( "%s: rendering data started" % (self.mTracker,) )

        result = []
        for group, data in self.mData.iteritems():
            lines = self.render( data ) 
            if lines and len(self.mData) > 1 and SECTION_TOKEN:
                result.extend( ["*%s*" % group, ""] )
                # result.extend( [ SECTION_TOKEN * len(group), group, SECTION_TOKEN * len(group), "" ] )
            if lines: result.extend( lines )

        debug( "%s: rendering data finished with %i lines and %i plots" % (self.mTracker, len(result), len(_pylab_helpers.Gcf.get_all_fig_managers() ) ) )

        return result

    def render(self, data):
        """return a list of lines in rst format.

        This is the principal method that should be re-defined
        in subclasses of :class:`Renderer:Renderer`.
        """
        return []

    def __call__(self, *args, **kwargs ):
        self.prepare( *args, **kwargs )
        self.collectData()
        return self.commit()

class RendererStats(Renderer):
    """Basic statistical location parameters.

    Requires :class:`DataTypes.SingleColumnData`.
    """
    mRequiredType = type( SingleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )

    def addData( self, group, title, data ):
        try:
            self.mData[group].append( (title,Stats.Summary( data ) ) )
        except ValueError, msg:
            debug( "could not compute stats for %s: %s %s" % (group,title,msg) )

    def render(self, data):
        lines = []
        if len(data) == 0: return lines
        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "track","%s" ' % '","'.join( Stats.Summary().getHeaders() ) )
        lines.append( '')
        for track, stats in data:
            lines.append( '   "%s","%s"' % (track, '","'.join( str(stats).split("\t")) ) )
        lines.append( "") 

        return lines

class RendererTable(Renderer):    
    """A table with numerical columns.

    It only implements column wise transformations.

    This class adds the following options to the :term:`render` directive.

       :term:`normalized-max`: normalize data by maximum.

       :term:`normalized-total`: normalize data by total.

       :term:`add-total`: add a total field.

    Requires :class:`DataTypes.LabeledData`.
    """

    mRequiredType = type( LabeledData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        Renderer.prepare( self, *args, **kwargs )
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

    def addData( self, group, title, data ):
        self.mData[group].append( (title, data ) )

    def getHeaders( self, data ):
        """return a list of headers and a mapping of header to column."""
        # preserve the order of columns
        headers = {}
        sorted_headers = []
        for track, d in data:
            for h, v in d:
                if h not in headers: 
                    headers[h] = len(headers)
                    sorted_headers.append(h)

        return sorted_headers, headers

    def convertData( self, data ):
        """apply converters to the data.

        The data is a tuple of (track, data) with each data
        a tuple of (header, value).

        The same data structure is returned.

        If there is an error during conversion, values will
        be set to None.
        """
        new_data = []
        for track, table in data:
            columns = [x[0] for x in table] 
            if len(columns) == 0: continue
            values = numpy.array( [x[1] for x in table] )
            if not values.any(): continue
            
            try:
                for convert in self.mConverters: values = convert( values )
            except ZeroDivisionError:
                values = [ None ] * len(table) 
            new_data.append( (track, zip( columns, values )) )
        return new_data

    def render(self, data):
        lines = []
        data = self.convertData( data )
        if len(data) == 0: return lines

        sorted_headers, headers = self.getHeaders(data)
        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        if self.mAddTotal:
            lines.append( '   :header: "track","total","%s" ' % '","'.join( sorted_headers ) )
        else:
            lines.append( '   :header: "track","%s" ' % '","'.join( sorted_headers ) )

        lines.append( '')

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
                lines.append( '   "%s","%s","%s"' % (track, total, '","'.join( [ toValue(dd, x) for x in sorted_headers ] ) ) )
        else:
            for track, d in data:
                dd = dict(d)
                lines.append( '   "%s","%s"' % (track, '","'.join( [ toValue(dd, x) for x in sorted_headers ] ) ) )

        lines.append( "") 

        return lines

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

    Requires :class:`DataTypes.LabeledData`
    """
    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        RendererTable.prepare( self, *args, **kwargs )

        self.mConverters = []        
        if "transform-matrix" in kwargs:
            for kw in [x.strip() for x in kwargs["transform-matrix"].split(",")]:
                if kw == "correspondence-analysis":
                    self.mConverters.append( self.transformCorrespondenceAnalysis )
                elif kw == "normalized-row-total":
                    self.mConverters.append( self.transformNormalizeRowTotal )
                    self.mFormat = "%6.4f"
                elif kw == "normalized-row-max":
                    self.mConverters.append( self.transformNormalizeRowMax )
                    self.mFormat = "%6.4f"
                elif kw == "normalized-column-total":
                    self.mConverters.append( self.transformNormalizeColumnTotal )
                    self.mFormat = "%6.4f"
                elif kw == "normalized-column-max":
                    self.mConverters.append( self.transformNormalizeColumnMmax )
                    self.mFormat = "%6.4f"

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

    def transformNormalizeColumn_max( self, matrix, rows, cols ):
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


        Returns a tuple (matrix, rows, colums).
        """

        rows = [ x[0] for x in data ]
        columns = []
        for t,vv in data: columns.extend( [x[0] for x in vv ] )
        columns = sorted(list(set(columns)))
        map_column2index = dict( [(x[1],x[0]) for x in enumerate( columns ) ] )
        matrix = numpy.array( [missing_value] * (len( rows) * len(columns) ), numpy.float)
        matrix.shape = (len(rows), len(columns) )
        x = 0 
        for track, vv in data:
            for column, value in vv:
                matrix[x, map_column2index[column]] = value
            x += 1

        for converter in self.mConverters: matrix, rows, columns = converter(matrix, rows, columns)

        return matrix, rows, columns

    def render( self, data ):
        """render the data."""
        matrix, rows, columns = self.buildMatrix( data )
        lines = []
        if len(rows) == 0: return lines

        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "track","%s" ' % '","'.join( columns ) )
        lines.append( '')
        for x in range(len(rows)):
            lines.append( '   "%s","%s"' % (rows[x], '","'.join( [ self.mFormat % x for x in matrix[x,:] ] ) ) )
        lines.append( "") 
        return lines

class RendererInterleavedBars(RendererTable, Plotter):
    """Stacked bars

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererTable.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs):
        RendererTable.prepare( self, *args, **kwargs )
        Plotter.prepare( self, *args, **kwargs )

        self.mFormat = "%i"

    def render( self, data ):
        
        self.startPlot( data )

        lines, legend = [], []

        nplotted = 0
        nskipped = 0

        sorted_headers, headers = self.getHeaders(data)

        data = self.convertData( data )
        width = 1.0 / (len(sorted_headers) + 1 )

        legend, plts = [], []

        tracks = [ x[0] for x in data ]
        
        xvals = numpy.arange( 0, len(tracks) )
        offset = width / 2.0
        
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

    def prepare(self, *args, **kwargs):
        RendererTable.prepare( self, *args, **kwargs )
        Plotter.prepare( self, *args, **kwargs )

        self.mFormat = "%i"

    def render( self, data ):

        sorted_headers, headers = self.getHeaders(data)
        data = self.convertData( data )

        if len(data) == 0: return []
        
        self.startPlot( data )

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

        result = []
        matrix, rows, columns = self.buildMatrix( data )
        result.extend(self.plotMatrix( matrix, rows, columns ) )

        return result

class RendererBoxPlot(Renderer, Plotter):        
    """Histogram as plot.

    Requires :class:`DataTypes.SingleColumnData`.
    """
    mRequiredType = type( SingleColumnData( None ) )
    
    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def prepare(self, *args, **kwargs ):

        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )
        
    def render(self, data ):

        self.startPlot( data )

        plts, legend = [], []
        nplotted = 0

        all_data = []
        for track, values in data:
            all_data.append( [ x for x in values if x != None ] )
            legend.append( track )

        plts.append( plt.boxplot( all_data ) )
        
        if len( legend ) > 5 or max( [len(x) for x in legend] ) >= 8 : 
            rotation = "vertical"
        else: 
            rotation = "horizontal"

        plt.xticks( [ x + 1 for x in range(0,len(legend)) ],
                    legend,
                    rotation = rotation,
                    fontsize="8" )

        return self.endPlot( plts, None )

class RendererHistogram(Renderer ):        
    """Histogram as table.

    Requires :class:`DataTypes.SingleColumnData`.
    """

    bin_marker = "left"
    mRequiredType = type( SingleColumnData( None ) )

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs ):

        Renderer.prepare( self, *args, **kwargs )

        self.mConverters = []
        self.mFormat = "%i"
        self.mBins = "100"
        self.mRange = None

        if "normalized-max" in kwargs:
           self.mConverters.append( self.normalize_max )
           self.mFormat = "%6.4f"
        if "normalized-total" in kwargs:
           self.mConverters.append( self.normalize_total )
           self.mFormat = "%6.4f"
        if "cumulative" in kwargs:
            self.mConverters.append( self.cumulate )
        if "reverse-cumulative" in kwargs:
            self.mConverters.append( self.reverse_cumulate )

        if "bins" in kwargs: self.mBins = kwargs["bins"]
        # removed eval
        if "range" in kwargs: self.mRange = kwargs["range"]

    def addData( self, group, title, data ):

        # remove None values
        ndata = [ x for x in data if x != None ]
        nremoved = len(data) - len(ndata)
        if nremoved:
            warn( "removed %i None values from %s: %s: %s" % (nremoved, str(self.mTracker), group, title) )

        data = ndata

        if len(data) == 0: 
            warn( "no data for %s: %s: %s" % (str(self.mTracker), group, title ) )
            return

        binsize = None

        if self.mRange != None: 
            vals = [ x.strip() for x in self.mRange.split(",") ]
            if len(vals) == 3: mi, ma, binsize = vals[0], vals[1], float(vals[2])
            elif len(vals) == 2: mi, ma, binsize = vals[0], vals[1], None
            elif len(vals) == 1: mi, ma, binsize = vals[0], None, None
            if mi == "": mi = min(data)
            else: mi = float(mi)
            if ma == "": ma = max(data)
            else: ma = float(ma)
        else:
            mi, ma= min( data ), max(data)

        if self.mBins.startswith("log"):
            a,b = self.mBins.split( "-" )
            nbins = float(b)
            if ma < 0: raise ValueError( "can not bin logarithmically for negative values.")
            if mi == 0: mi = numpy.MachAr().epsneg
            ma = log10( ma )
            mi = log10( mi )
            bins = [ 10 ** x for x in arange( mi, ma, ma / nbins ) ]
        elif binsize != None:
            bins = arange(mi, ma, binsize )
        else:
            bins = eval(self.mBins)

        if hasattr( bins, "__iter__") and len(bins) == 0:
            warn( "empty bins from %s: %s: %s" % (str(self.mTracker), group, title) )
            return

        self.mData[group].append( (title, numpy.histogram( data, bins=bins, range=(mi,ma), new = True ), nremoved ) )

    def cumulate( self, data ):
        return data.cumsum()
    
    def reverse_cumulate( self, data ):
        return data[::-1].cumsum()[::-1]

    def binToX( self, bins ):
        """convert bins to x-values."""
        if self.bin_marker == "left": return bins[:-1]
        elif self.bin_marker == "mean": 
            return [ (bins[x] - bins[x-1]) / 2.0 for x in range(1,len(bins)) ]
        elif self.bin_marker == "right": return bins[1:]

    def render(self, data):
        
        if len(data) == 0: return []

        hh = []
        for track, histogram, nremoved in data:
            d, bins = histogram
            for convert in self.mConverters: d = convert(d)
            hh.append( Histogram.Convert( d, 
                                          self.binToX(bins), 
                                          no_empty_bins = True ) )

        h = Histogram.Combine( hh, missing_value = "na" )
        
        def toValue( x ):
            if x != "na": return self.mFormat % x
            else: return x

        lines = []
        lines.append( ".. csv-table:: %s" % self.mTracker.getShortCaption() )
        lines.append( '   :header: "bin","%s" ' % '","'.join( [x[0] for x in data]) )
        lines.append( "")
        for bin, values in h:
            lines.append( '   "%s","%s"' % (bin, '","'.join( [toValue(x) for x in values ] ) ) )
        lines.append( "") 

        return lines

class RendererHistogramPlot(RendererHistogram, Plotter):        
    """Histogram as plot.

    Requires :class:`DataTypes.SingleColumnData`.
    """

    def __init__(self, *args, **kwargs):
        RendererHistogram.__init__(self, *args, **kwargs )
        Plotter.__init__(self, *args, **kwargs )

    def prepare(self, *args, **kwargs ):

        RendererHistogram.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )
        
        f = []
        if self.normalize_total in self.mConverters: f.append( "relative" )
        else: f.append( "absolute" )
        if self.cumulate in self.mConverters: f.append( "cumulative" )
        if self.reverse_cumulate in self.mConverters: f.append( "cumulative" )
        f.append("frequency")

        self.mYLabel = " ".join(f)

    def render(self, data):
        """returns a placeholder."""
        
        self.startPlot( data )

        plts, legend = [], []

        nplotted = 0

        for track, histogram, nremoved in data:

            s = self.mSymbols[nplotted % len(self.mSymbols)]

            # get and transform x/y values
            yvals, bins = histogram
            xvals = self.binToX( bins )
            for convert in self.mConverters: yvals = convert( yvals )
        
            plts.append(plt.plot( xvals,
                                  yvals,
                                  s ) )
            legend.append( track )
            nplotted += 1

        return self.endPlot( plts, legend )

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

        return lines

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

        result = []

        tests = self.getTestResults( data )
        if len(tests) == 0: return result

        for track, vv in data:

            if SUBSECTION_TOKEN:
                #result.extend( [track, SUBSECTION_TOKEN * len(track), "" ] )
                result.extend( ["*%s*" % track, "" ] )

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

            result.extend(self.plotMatrix( matrix, headers, headers ) )

        return result

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

        result = []

        tests = self.getTestResults( data )
        if len(tests) == 0: return result

        for track, vv in data:
            if SUBSECTION_TOKEN:
                result.extend( [track, SUBSECTION_TOKEN * len(track), "" ] )

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

            result.extend( self.endPlot( plts, headers) )

        return result

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

    def binToX( self, bins ):
        """convert bins to x-values."""
        if self.bin_marker == "left": return bins[:-1]
        elif self.bin_marker == "mean": 
            return [ (bins[x] - bins[x-1]) / 2.0 for x in range(1,len(bins)) ]
        elif self.bin_marker == "right": return bins[1:]

    def addData( self, group, title, data ):
        self.mData[group].append( (title,data) )

    def prepare(self, *args, **kwargs ):

        Renderer.prepare( self, *args, **kwargs )
        Plotter.prepare(self, *args, **kwargs )
        
    def render(self, data):
        """returns a placeholder."""
        
        result = []

        for track, vv in data:

            self.startPlot( data )
            headers, columns = vv

            # get and transform x/y values
            xvals = self.binToX( columns[0] )

            plts, legend = [], []
            nplotted = 0
            for y in range( 1, len(columns) ):
                s = self.mSymbols[nplotted % len(self.mSymbols)]        
                yvals = columns[y]
                plts.append(plt.plot( xvals, yvals, s ) )
                legend.append( headers[y] )
                nplotted += 1

            result.extend( self.endPlot( plts, legend ) )

        return result

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
        return result


