import Stats
from logging import warn, log, debug, info
import itertools
import numpy
import odict

class Transformer(object):

    def __init__(self,*args,**kwargs):
        pass

class TransformerStats( Transformer ):
    '''compute stats on each column.'''

    def __call__(self, data ):
        debug( "%s: called" % str(self))
        for track,slices in data.iteritems():
            for slice, columns in slices.iteritems():
                for header,values in columns.iteritems():
                    try:
                        data[track][slice][header] = Stats.Summary( values )
                    except TypeError:
                        warn("%s: could not compute stats: expected an array of values, but got '%s'" % (str(self), str(values)) )
        return data

class TransformerCorrelation( Transformer ):
    '''for each pair of columns on the lowest level compute
    the correlation coefficient and other stats.
    '''

    def __call__(self, data ):
        debug( "%s: called" % str(self))
        for track,slices in data.iteritems():
            for slice, columns in slices.iteritems():
                pairs = itertools.combinations( columns.keys(), 2)
                new = {}
                for x,y in pairs:
                    xvals, yvals = data[track][slice][x], data[track][slice][y]
                    take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
                    xvals = [xvals[i] for i in take ]
                    yvals = [yvals[i] for i in take ]
                    
                    try:
                        result = Stats.doCorrelationTest( xvals, yvals )
                    except ValueError, msg:
                        continue
                    new[ "%s vs %s" % (x,y)] = result
                data[track][slice]=new
        return data


class TransformerHistogram( Transformer ):
    '''compute a histogram of values.'''
    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.mConverters = []
        self.mFormat = "%i"
        self.mBins = "100"
        self.mRange = None
        self.mBinMarker = "left"

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

        f = []
        if self.normalize_total in self.mConverters: f.append( "relative" )
        else: f.append( "absolute" )
        if self.cumulate in self.mConverters: f.append( "cumulative" )
        if self.reverse_cumulate in self.mConverters: f.append( "cumulative" )
        f.append("frequency")

        self.mYLabel = " ".join(f)

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

    def cumulate( self, data ):
        return data.cumsum()
    
    def reverse_cumulate( self, data ):
        return data[::-1].cumsum()[::-1]

    def binToX( self, bins ):
        """convert bins to x-values."""
        if self.mBinMarker == "left": return bins[:-1]
        elif self.mBinMarker == "mean": 
            return [ (bins[x] - bins[x-1]) / 2.0 for x in range(1,len(bins)) ]
        elif self.mBbinMarker == "right": return bins[1:]

    def toHistogram( self, data ):
        '''compute the histogram.'''
        ndata = [ x for x in data if x != None ]
        nremoved = len(data) - len(ndata)
        if nremoved:
            warn( "removed %i None values from %s: %s: %s" % (nremoved, str(self.mTracker), group, title) )

        data = ndata

        if len(data) == 0: 
            warn( "empty histogram" )
            return

        binsize = None

        if self.mRange != None: 
            vals = [ x.strip() for x in self.mRange.split(",") ]
            if len(vals) == 3: mi, ma, binsize = vals[0], vals[1], float(vals[2])
            elif len(vals) == 2: mi, ma, binsize = vals[0], vals[1], None
            elif len(vals) == 1: mi, ma, binsize = vals[0], None, None
            if mi == None or mi == "": mi = min(data)
            else: mi = float(mi)
            if ma == None or ma == "": ma = max(data)
            else: ma = float(ma)
        else:
            mi, ma= min( data ), max(data)

        if self.mBins.startswith("dict"):
            h = collections.defaultdict( int )
            for x in data: h[x] += 1
            bin_edges = sorted( h.keys() )
            hist = numpy.zeros( len(bin_edges), numpy.int )
            for x in range(len(bin_edges)): hist[x] = h[bin_edges[x]]
            bin_edges.append( bin_edges[-1] + 1 )
        else:
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
            hist, bin_edges = numpy.histogram( data, bins=bins, range=(mi,ma), new = True )
        
        return self.binToX(bin_edges), hist

    def __call__(self, data ):
        debug( "%s: called" % str(self))
        for track,slices in data.iteritems():
            for slice, columns in slices.iteritems():
                for header,values in columns.iteritems():
                    bins, values = self.toHistogram(data[track][slice][header])
                    data[track][slice][header] = odict.OrderedDict( ((header,bins), ("frequency", values)) )
        return data
    
