import Stats
from logging import warn, log, debug, info
import itertools
import numpy
import odict
from DataTree import DataTree

class Transformer(object):

    nlevels = None

    def __init__(self,*args,**kwargs):
        pass

    def __call__(self, data ):

        if self.nlevels == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        labels = data.getPaths()        
        assert len(labels) >= self.nlevels, "expected at least %i levels - got %i" % (self.nlevels, len(labels))
        
        paths = list(itertools.product( *labels[:-self.nlevels] ))
        for path in paths:
            work = data.getLeaf( path )
            if not work: continue
            data.setLeaf( path,
                          self.transform( work, path ) )

        return data
        
class TransformerFilter( Transformer ):
    '''select columns in the deepest dictionary.
    '''
    
    nlevels = 1
    default = 0

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.filter = set(kwargs["tf-fields"].split(","))
        except KeyError: 
            raise KeyError( "TransformerFilter requires the `tf-fields` option to be set." )

        try: self.nlevels = int(kwargs["tf-level"])
        except KeyError: 
            pass
                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        for v in data.keys():
            if v not in self.filter:
                del data[v]
            
        return data

class TransformerSelect( Transformer ):
    '''replace the lowest hierarchy with a single value.
    '''
    
    nlevels = 2
    default = 0

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = kwargs["tf-fields"]
        except KeyError: 
            raise KeyError( "TransformerSelect requires the `tf-fields` option to be set." )
                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        for v in data.keys():
            try:
                data[v] = data[v][self.fields]
            except KeyError:
                data[v] = self.default
            
        return data

class TransformerCombinations( Transformer ):
    '''build combinations of the second lowest level.
    '''
    
    nlevels = 2

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = kwargs["tf-fields"]
        except KeyError: 
            raise KeyError( "TransformerCombinations requires the `tf-fields` option to be set." )

    def transform(self, data, path):
        debug( "%s: called" % str(self))

        vals =  data.keys()
        new_data = odict.OrderedDict()
        for x1 in range(len(vals)-1):
            n1 = vals[x1]
            d1 = data[n1][self.fields]
            for x2 in range(x1+1, len(vals)):
                n2 = vals[x2]
                d2 = data[n2][self.fields]
                if len(d1) != len(d2):
                    raise ValueError("length of elements not equal: %i != %i" % (len(d1), len(d2)))
                key = "%s vs %s" % (n1,n2)
                new_data[key] =\
                    odict.OrderedDict( (\
                        ("%s/%s" % (n1,self.fields), d1),
                        ("%s/%s" % (n2,self.fields), d2), ) )
        print new_data.keys()

        return new_data

class TransformerStats( Transformer ):
    '''compute stats on each column.'''
    nlevels = 1

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))
        for header, values in data.iteritems():
            try:
                data[header] =  Stats.Summary( values )
            except TypeError:
                warn("%s: could not compute stats: expected an array of values, but got '%s'" % (str(self), str(values)) )
        return data

class TransformerCorrelation( Transformer ):
    '''for each pair of columns on the lowest level compute
    the correlation coefficient and other stats.
    '''

    nlevels = 1

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))

        if len(data.keys()) < 2:
            raise ValueError( "can not compute correlation with only a single array." )

        pairs = itertools.combinations( data.keys(), 2)

        new_data = odict.OrderedDict()

        for x,y in pairs:
            xvals, yvals = data[x], data[y]
            take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
            xvals = [xvals[i] for i in take ]
            yvals = [yvals[i] for i in take ]

            try:
                result = Stats.doCorrelationTest( xvals, yvals )
            except ValueError, msg:
                continue
            new_data[ "%s vs %s" % (x,y)] = result

        return new_data

class TransformerHistogram( Transformer ):
    '''compute a histogram of values.'''

    nlevels = 1

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
            hist, bin_edges = numpy.histogram( data, bins=bins, range=(mi,ma) )
        
        return self.binToX(bin_edges), hist

    def transform(self, data, path):
        debug( "%s: called" % str(self))

        for header, values in data.iteritems():
            bins, values = self.toHistogram(values)
            data[header] =  odict.OrderedDict( ((header,bins), ("frequency", values)) )
        return data
