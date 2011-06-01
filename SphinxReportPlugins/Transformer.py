from logging import warn, log, debug, info
import itertools
import numpy
from numpy import arange

from SphinxReport.odict import OrderedDict as odict
from SphinxReport.DataTree import DataTree
from SphinxReport.Component import *
from SphinxReport import Stats

from docutils.parsers.rst import directives

# ignore numpy histogram warnings in versions 1.3
import warnings

class Transformer(Component):

    capabilities = ['transform']

    nlevels = None

    def __init__(self,*args,**kwargs):
        pass

    def __call__(self, data ):

        if self.nlevels == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        labels = data.getPaths()        
        debug( "transform: started with paths: %s" % labels)
        assert len(labels) >= self.nlevels, "expected at least %i levels - got %i" % (self.nlevels, len(labels))
        
        paths = list(itertools.product( *labels[:-self.nlevels] ))
        for path in paths:
            work = data.getLeaf( path )
            if not work: continue
            new_data = self.transform( work, path )
            if new_data:
                data.setLeaf( path, new_data )
            else:
                warn( "no data at %s - removing branch" % str(path))
                data.removeLeaf( path )

        debug( "transform: finished with paths: %s" % data.getPaths())

        return data
        
class TransformerFilter( Transformer ):
    '''select columns in the deepest dictionary.
    '''
    
    nlevels = 1
    default = 0

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged),
          ('tf-level', directives.length_or_unitless) )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.filter = set(kwargs["tf-fields"].split(","))
        except KeyError: 
            raise KeyError( "TransformerFilter requires the `tf-fields` option to be set." )

        try: self.nlevels = int(kwargs["tf-level"])
        except KeyError: pass
                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        for v in data.keys():
            if v not in self.filter:
                del data[v]
            
        return data

class TransformerIndicator( Transformer ):
    '''take a field from the lowest level and
    build and indicator out of it.
    '''
    
    nlevels = 1
    default = 0

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged),
          ('tf-level', directives.length_or_unitless) )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try:
            self.filter = kwargs["tf-fields"]
        except KeyError: 
            raise KeyError( "TransformerFilter requires the `tf-fields` option to be set." )

        try: self.nlevels = int(kwargs["tf-level"])
        except KeyError: pass

                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        vals = data[self.filter]
        return odict(zip( vals, [1] * len(vals) ))

class TransformerSelect( Transformer ):
    '''replace the lowest hierarchy with a single value.
    '''
    
    nlevels = 2
    default = 0

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged), )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = kwargs["tf-fields"].split(",")
        except KeyError: 
            raise KeyError( "TransformerSelect requires the `tf-fields` option to be set." )
                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        nfound = 0
        for v in data.keys():
            for field in self.fields:
                try:
                    data[v] = data[v][field]
                    nfound += 1
                    break
                except KeyError: 
                    pass
            else:
                data[v] = self.default
                    
        if nfound == 0:
            raise ValueError("could not find any field from `%s` in %s" % (str(self.fields), path))

        return data

class TransformerGroup( Transformer ):
    '''group second-to-last level by lowest level.

    For example:

    track1/gene_id=1, track1/gene_name=1
    track2/gene_id=1, track2/gene_name=2

    with tf-fields=gene_id

    will become:

    gene_id1/gene_name=1
    gene_id1/tracks = [track1,track2]

    Note that other fields not in the group field will take the value of the first row.
    '''
    
    nlevels = 2
    default = 0

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged), )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = kwargs["tf-fields"].split(",")
        except KeyError: 
            raise KeyError( "TransformerGroup requires the `tf-fields` option to be set." )

        if len(self.fields) != 1:
            raise ValueError("`tf-fields` requires exactly one field for grouping function" )
        
        self.field = self.fields[0]

    def transform(self, data, path):
        debug( "%s: called" % str(self))

        nfound = 0
        new_data = odict()

        for v in data.keys():
            other_fields = [ x for x in data[v].keys() if x != self.field ]
            for pos, val in enumerate(data[v][self.field]):
                if val not in new_data: new_data[val] = odict()
                if "group" not in new_data[val]: 
                    for o in other_fields:
                        new_data[val][o] = data[v][o][pos]
                    new_data[val]["group"] = ""
                new_data[val]["group"] += ",%s" % v

        return new_data

class TransformerCombinations( Transformer ):
    '''build combinations of the second lowest level.

    input:
    a/1/x
    a/2/x
    a/3/x
    b/1/x
    b/2/x

    Output:
    

    '''
    
    nlevels = 2

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged), )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = kwargs["tf-fields"]
        except KeyError: 
            raise KeyError( "TransformerCombinations requires the `tf-fields` option to be set." )

    def transform(self, data, path):

        debug( "%s: called" % str(self))

        vals =  data.keys()
        new_data = DataTree()

        for x1 in range(len(vals)-1):
            n1 = vals[x1]
            d1 = data[n1][self.fields]
            for x2 in range(x1+1, len(vals)):
                n2 = vals[x2]
                d2 = data[n2][self.fields]
                ## check if array?
                if len(d1) != len(d2):
                    raise ValueError("length of elements not equal: %i != %i" % (len(d1), len(d2)))
                
                new_data.setLeaf( ( ("%s x %s" % (n1, n2) ), n1),
                                  d1 )

                new_data.setLeaf( ( ("%s x %s" % (n1, n2) ), n2),
                                  d2 )
                                  
        return new_data

class TransformerStats( Transformer ):
    '''compute summary statistics.

    Empty paths will be removed.
    '''
    nlevels = 1

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))
        for header, values in data.iteritems():
            if len(values) == 0: 
                warn( "empty histogram for %s -removing" % header)
                del data[header]
                continue
            
            try:
                data[header] = Stats.Summary( values )._data
            except TypeError:
                warn("%s: could not compute stats: expected an array of values, but got '%s'" % (str(self), str(values)) )
                del data[header]
            except ValueError, msg:
                warn("%s: could not compute stats: '%s'" % (str(self), msg) )
                del data[header]

        return data

class TransformerPairwise( Transformer ):
    '''for each pair of columns on the lowest level compute
    the pearson correlation coefficient and other stats.
    '''

    nlevels = 1
    method = None
    paired = False

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))

        if len(data.keys()) < 2:
            raise ValueError( "expected at least two arrays, got only %s." % str(data.keys()) )

        pairs = itertools.combinations( data.keys(), 2)

        new_data = odict()

        for x in data.keys(): new_data[x] = odict()
        
        for x,y in pairs:
            xvals, yvals = data[x], data[y]
            if self.paired:
                if len(xvals) != len(yvals):
                    raise ValueError("expected to arrays of the same length, %i != %i" % (len(xvals),
                                                                                          len(yvals)))
                take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None ]
                xvals = [xvals[i] for i in take ]
                yvals = [yvals[i] for i in take ]

            try:
                result = self.apply( xvals, yvals )
            except ValueError, msg:
                warn( "pairwise computation failed: %s" % msg)
                continue

            new_data[x][y] = result
            new_data[y][x] = result

        return new_data

class TransformerCorrelation( TransformerPairwise ):
    '''compute correlations.'''
    paired = True
    def apply( self, xvals, yvals ):
        return Stats.doCorrelationTest( xvals, yvals, method = self.method )

class TransformerCorrelationPearson( TransformerCorrelation ):
    '''for each pair of columns on the lowest level compute
    the spearman correlation coefficient and other stats.
    '''
    method = "pearson"

class TransformerCorrelationSpearman( TransformerCorrelation ):
    '''for each pair of columns on the lowest level compute
    the spearman correlation coefficient and other stats.
    '''
    method = "spearman"

class TransformerMannWhitneyU( TransformerPairwise ):
    '''apply the Mann-Whitney U test to test for 
    the difference of medians.
    '''

    def apply( self, xvals, yvals ):
        xx = numpy.array( [ x for x in xvals if x != None ] )
        yy = numpy.array( [ y for y in yvals if y != None ] )
        return Stats.doMannWhitneyUTest( xx, yy )
    
class TransformerHistogram( Transformer ):
    '''compute a histogram of values.'''

    nlevels = 1

    options = Transformer.options +\
        ( ('tf-aggregate', directives.unchanged), 
          ('tf-bins', directives.unchanged), 
          ('tf-range', directives.unchanged), 
          )

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.mConverters = []
        self.mFormat = "%i"
        self.mBinMarker = "left"

        self.mMapKeyword = {
            "normalized-max" : self.normalize_max,
            "normalized-total" : self.normalize_total,
            "cumulative" : self.cumulate,
            "reverse-cumulative": self.reverse_cumulate,
            }

        if "tf-aggregate" in kwargs:
            for x in kwargs["tf-aggregate"].split(","):
                try:
                    self.mConverters.append( self.mMapKeyword[x ] )
                except KeyError:
                    raise KeyError("unknown keyword `%s`" % x)
                
        if self.normalize_total in self.mConverters or self.normalize_max in self.mConverters:
           self.mFormat = "%6.4f" 

        self.mBins = kwargs.get( "tf-bins", "100" )
        self.mRange = kwargs.get( "tf-range", None )

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
            warn( "removed %i None values" % nremoved )

        data = ndata

        if len(data) == 0: 
            warn( "empty histogram" )
            return None, None

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

                try:
                    a,b = self.mBins.split( "-" )
                except ValueError:
                    raise SyntaxError( "expected log-xxx, got %s" % self.mBins )
                nbins = float(b)
                if ma < 0: raise ValueError( "can not bin logarithmically for negative values.")
                if mi == 0: mi = numpy.MachAr().epsneg
                ma = numpy.log10( ma )
                mi = numpy.log10( mi )
                bins = [ 10 ** x for x in arange( mi, ma, ma / nbins ) ]
            elif binsize != None:
                # make sure that ma is part of bins
                data.sort()
                bins = numpy.arange(mi, ma + binsize, binsize )
            else:
                try:
                    bins = eval(self.mBins)
                except SyntaxError, msg:
                    raise SyntaxError( "could not evaluate bins from `%s`, error=`%s`" \
                                           % (self.mBins, msg))


            if hasattr( bins, "__iter__") and len(bins) == 0:
                warn( "empty bins")
                return None, None

           # ignore histogram semantics warning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                hist, bin_edges = numpy.histogram( data, bins=bins, range=(mi,ma) )
        
        return self.binToX(bin_edges), hist

    def transform(self, data, path):
        debug( "%s: called" % str(self))

        to_delete = set()
        for header, values in data.iteritems():
            bins, values = self.toHistogram(values)
            if bins != None:
                for converter in self.mConverters: values = converter(values)
                data[header] =  odict( ((header,bins), ("frequency", values)) )
            else:
                to_delete.add( header )

        for header in to_delete:
            del data[header]
        return data
