from logging import warn, log, debug, info
import itertools
import numpy
from numpy import arange

from SphinxReport.odict import OrderedDict as odict
from SphinxReport.Component import *
from SphinxReport import Stats, DataTree, Utils

from docutils.parsers.rst import directives

# for rpy2 for data frames
import rpy2
from rpy2.robjects import r as R

# ignore numpy histogram warnings in versions 1.3
import warnings

########################################################################
########################################################################
########################################################################
class Transformer(Component):
    '''Base class for transformers.

    Implements the basic __call__ method that iterates over a :term:`data tree`
    and calls self.transform method on the appropriate levels in the
    hierarchy.
    '''

    capabilities = ['transform']

    nlevels = None

    def __init__(self,*args,**kwargs):
        pass

    def __call__(self, data ):

        if self.nlevels == None: raise NotImplementedError("incomplete implementation of %s" % str(self))

        labels = DataTree.getPaths( data )        
        debug( "transform: started with paths: %s" % labels)
        assert len(labels) >= self.nlevels, "expected at least %i levels - got %i" % (self.nlevels, len(labels))
        
        paths = list(itertools.product( *labels[:-self.nlevels] ))
        for path in paths:
            work = DataTree.getLeaf( data, path )
            if not work: continue
            new_data = self.transform( work, path )
            if new_data:
                if path:
                    DataTree.setLeaf( data, path, new_data )
                else:
                    # set new root
                    data = new_data
            else:
                warn( "no data at %s - removing branch" % str(path))
                DataTree.removeLeaf( data, path )

        debug( "transform: finished with paths: %s" % DataTree.getPaths( data ))

        return data
        
########################################################################
########################################################################
## Conversion transformers
########################################################################
########################################################################
class TransformerToLabels( Transformer ):
    '''convert :term:`numerical arrays` to :term:`labeled data`.

    By default, the items are labeled numerically. If `tf-labels`
    is given it is used instead.

    Example::

       Input:                 Returns:
       a/keys/['x','y','z']   a/x/1
       a/values/[4,5,6]       a/y/2
                              a/z/3


    '''
    nlevels = 1

    options = Transformer.options +\
        ( ('tf-labels', directives.unchanged), )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        self.labels = kwargs.get("tf-labels", None)
        
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        if len(data) == 0: return data
        
        keys = data.keys()

        if self.labels: 
            labels = data[self.labels]
            del keys[keys.index(self.labels)]
            if len(keys) < 1: 
                raise ValueError( "TransformerToLabels requires at least two arrays, got only 1, if tf-labels is set" )
        else: 
            max_nkeys = max([len(x) for x in data.values() ])
            labels = range(1, max_nkeys + 1)

        labels = map(str, labels)

        if len(data) == 2:
            new_data = odict(zip(labels, data[keys[0]]))
        else:
            new_data = odict()
            for key in keys:
                new_data[key] = odict(zip(labels, data[key]))
                
        return new_data

########################################################################
########################################################################
########################################################################
class TransformerToList( Transformer ):
    '''transform categorized data into lists.

    Example::

       Input:            Returns:
       a/x/1             x/[1,4]
       a/y/2             y/[2,5]
       a/z/3             z/[3,6]
       b/x/4
       b/y/5
       b/z/6
       
    '''
    nlevels = 2
    
    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))

        lists = odict()

        for major_key, values in data.iteritems():
            for minor_key, value in values.iteritems():
                if minor_key in lists:
                    lists[minor_key].append( value )
                else:
                    lists[minor_key] = [value]

        sizes = [ len(x) for x in lists.values() ]
        if max(sizes) != min(sizes):
            warn( "%s: list of unequal sizes: min=%i, max=%i" %\
                      (self, min(sizes), max(sizes)))
        return lists

########################################################################
########################################################################
########################################################################
class TransformerToDataFrame( Transformer ):
    '''transform data into one or more data frames.

    Example::

       Input:                                Output:
       experiment1/expression = [1,2,3]      experiment1/df({ expression : [1,2,3], counts : [3,4,5] })
       experiment1/counts = [3,4,5]          experiment2/df({ expression : [8,9,1], counts : [4,5,6] })
       experiment2/expression = [8,9,1]
       experiment2/counts = [4,5,6]

    '''
    nlevels = 1
    
    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))

        t = odict()
        for minor_key, values in data.iteritems():
            if not Utils.isArray(values): raise ValueError("expected a list for data frame creation, got %s", type(data))
            if len(values) == 0: raise ValueError( "empty list for %s:%s" % (major_key, minor_key))
            v = values[0]
            if Utils.isInt( v ):
                t[minor_key] = rpy2.robjects.IntVector( values )
            elif Utils.isFloat(v):
                t[minor_key] = rpy2.robjects.FloatVector( values )
            else:
                t[minor_key] = rpy2.robjects.StrVector( values )

        return rpy2.robjects.DataFrame(t)

########################################################################
########################################################################
########################################################################
class TransformerIndicator( Transformer ):
    '''take a field from the lowest level and
    build an absent/present indicator out of it.
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

########################################################################
########################################################################
## Filtering transformers
########################################################################
########################################################################

########################################################################
########################################################################
########################################################################
########################################################################
class TransformerFilter( Transformer ):
    '''select fields from the deepest level in the hierarchy.

    This transformer removes all branches in a :term:`data tree`
    on level :term:`tf-level` that do not match the 
    :term:`tf-fields` option.

    Level is counted from the deepest branch. By default,
    leaves (level = 1) are removed.

    The following operations are perform when :term:`tf-fields` is set
    to ``x``::
       Input:          Returns:
       a/x=1            a/x=1
       a/y=2            b/x=3
       b/x=3
       b/y=4

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

        self.nlevels = int(kwargs.get("tf-level", self.nlevels) )
                          
    def transform(self, data, path):
        debug( "%s: called" % str(self))

        for v in data.keys():
            if v not in self.filter:
                del data[v]
            
        return data

########################################################################
########################################################################
########################################################################
class TransformerSelect( Transformer ):
    '''replace the lowest hierarchy with a single value.
    This transformer removes all branches in a :term:`data tree`
    on level :term:`tf-level` that do not match the 
    :term:`tf-fields` option.

    The following operations are perform when :term:`tf-fields` is set
    to ``x``::
       Input:          Returns:
       a/x=1            a=1
       a/y=2            b=3
       b/x=3
       b/y=4
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

########################################################################
########################################################################
########################################################################
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

    For example::

       Input:    Output:
       a/x=1     x/y=1
       a/y=1     x/tracks[a,b]
       b/x=1     
       b/y=2


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

########################################################################
########################################################################
########################################################################
class TransformerCombinations( Transformer ):
    '''build combinations of the second lowest level.

    For example::

       Input:      Output:
       a/x=1       a x b/a/x=1
       b/x=2       a x b/b/x=2
       c/x=3       a x c/a/x=1
                   a x c/b/x=2
                   b x c/a/x=2
                   b x c/a/x=3

    Uses the ``tf-fields`` option to combine a certain field.
    Otherwise, it combines the first data found.

    '''
    
    nlevels = 2

    options = Transformer.options +\
        ( ('tf-fields', directives.unchanged), )

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

        try: self.fields = set(kwargs["tf-fields"].split(","))
        except KeyError: 
            self.fields = None

    def transform(self, data, path):

        debug( "%s: called" % str(self))

        vals =  data.keys()
        new_data = odict()

        for x1 in range(len(vals)-1):
            n1 = vals[x1]
            # find the first field that fits
            if self.fields:
                for field in self.fields:
                    if field in data[n1]:
                        d1 = data[n1][field]
                        break
                else:
                    raise KeyError("could not find any match from '%s' in '%s'" % (str(data[n1].keys()), str(self.fields )))
            else:
                d1 = data[n1]

            for x2 in range(x1+1, len(vals)):
                n2 = vals[x2]
                if self.fields:
                    try:
                        d2 = data[n2][field]
                    except KeyErrror:
                        raise KeyError("no field %s in '%s'" % sttr(data[n2]))
                else:
                    d2 = data[n2]

                ## check if array?
                if len(d1) != len(d2):
                    raise ValueError("length of elements not equal: %i != %i" % (len(d1), len(d2)))
                
                DataTree.setLeaf( new_data, ( ("%s x %s" % (n1, n2) ), n1),
                                  d1 )

                DataTree.setLeaf( new_data, ( ("%s x %s" % (n1, n2) ), n2),
                                  d2 )
                                  
        return new_data

########################################################################
########################################################################
########################################################################
class TransformerStats( Transformer ):
    '''Compute summary statistics

    For example::

       Input:      
       [1,2,3,4,5,6,7,8,9,10

       Output:
       counts=10
       min=1
       max=10
       mean=5.5
       median=5.5
       samplestd=2.87
       sum=55
       q1=3
       q3=8
    '''
    nlevels = 1

    def __init__(self,*args,**kwargs):
        Transformer.__init__( self, *args, **kwargs )

    def transform(self, data, path ):
        debug( "%s: called" % str(self))
        # do not use iteritems as loop motifies dictionary

        to_delete = []
        for header, values in data.iteritems():
            if len(values) == 0: 
                warn( "no data for %s -removing" % header)
                to_delete.append( header )
                continue
            
            try:
                data[header] = Stats.Summary( values )._data
            except TypeError:
                warn("%s: could not compute stats: expected an array of values, but got '%s'" % (str(self), str(values)) )
                to_delete.append( header )
            except ValueError, msg:
                warn("%s: could not compute stats: '%s'" % (str(self), msg) )
                to_delete.append( header )

        for header in to_delete:
            del data[header]

        return data

########################################################################
########################################################################
########################################################################
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
                take = [i for i in range(len(xvals)) if xvals[i] != None and yvals[i] != None \
                            and type(xvals[i]) in (float,int,long) and type(yvals[i]) in (float,int,long) ]
                xvals = [xvals[i] for i in take ]
                yvals = [yvals[i] for i in take ]

            try:
                result = self.apply( xvals, yvals )
            except ValueError, msg:
                warn( "pairwise computation failed: %s" % msg)
                continue

            new_data[x][y] = result

        return new_data

class TransformerCorrelation( TransformerPairwise ):
    '''compute correlation test

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]

       Result:
       set1/set2/pvalue=0.0
       set1/set2/method=pearson
       set1/set2/nobservations=10
       set1/set2/coefficient=1.0
       set1/set2/alternative=two-sided
       set1/set2/logpvalue=0
       set1/set2/significance=***
    '''
    
    paired = True
    def apply( self, xvals, yvals ):
        r = Stats.doCorrelationTest( xvals, yvals, method = self.method )
        return Stats.doCorrelationTest( xvals, yvals, method = self.method )

class TransformerCorrelationPearson( TransformerCorrelation ):
    '''for each pair of columns on the lowest level compute
    the pearson correlation coefficient and other stats.

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]

       Output:
       set1/set2/pvalue=0.0
       set1/set2/method=pearson
       set1/set2/nobservations=10
       set1/set2/coefficient=1.0
       set1/set2/alternative=9
       set1/set2/logpvalue=0
       set1/set2/significance=***
       set1/set3/pvalue=
       ...
       set2/set3/pvalue=
       ...

    '''
    method = "pearson"

class TransformerCorrelationSpearman( TransformerCorrelation ):
    '''for each pair of columns on the lowest level compute
    the spearman correlation coefficient and other stats.

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]

       Output:
       set1/set2/pvalue=0.0
       set1/set2/method=spearman
       set1/set2/nobservations=10
       set1/set2/coefficient=1.0
       set1/set2/alternative=9
       set1/set2/logpvalue=0
       set1/set2/significance=***
       set1/set3/pvalue=0.0
       ...
       set2/set1/pvalue=0.0
       ...
       set2/set3/pvalue=0.0
       ...
       set3/set1/pvalue=0.0
       ...
       set3/set2/pvalue=0.0

    '''
    method = "spearman"

class TransformerMannWhitneyU( TransformerPairwise ):
    '''apply the Mann-Whitney U test to test for 
    the difference of medians.

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]

       Output:
       
    
    '''

    def apply( self, xvals, yvals ):
        xx = numpy.array( [ x for x in xvals if x != None ] )
        yy = numpy.array( [ y for y in yvals if y != None ] )
        r = Stats.doMannWhitneyUTest( xx, yy )
        return Stats.doMannWhitneyUTest( xx, yy )

class TransformerContingency( TransformerPairwise ):
    '''return number of identical entries

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]
             
       Output:
       set1/set2=8
       set1/set3=6
       set2/set1=8
       set2/set3=8
       set3/set1=6
       set3/set2=8
    '''

    paired = False
    def apply( self, xvals, yvals ):
        return len( set(xvals).intersection( set(yvals)) )

########################################################################
########################################################################
########################################################################
class TransformerAggregate( Transformer ):
    '''aggregate histogram like data.

    Example::

       Input:
       x=[ 1,1,1,1,1,2,2,2,4,4,5 ]
       frequency=[5,3,0,2,1]
     
       Output (with tf-aggregate=cumulative):
       x=[ 1.,1.8,2.6,3.4,4.2 ]
       frequency=[5,8,8,10,11]
     
    Possible aggregation options are:

    normalized-max
       normalize by maximum

    normalized-total
       normalize by total

    cumulative
       compute cumulative values

    reverse-cumulative
       compute reverse cumulative values

    relevel-with-first:
        add value of first bin to all other bins
        and set first bin to 0.

    '''

    nlevels = 1

    options = Transformer.options +\
        ( ('tf-aggregate', directives.unchanged), )

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
            "relevel-with-first": self.relevel_with_first,
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

    def relevel_with_first( self, data ):
        """re-level data - add value of first bin to all other bins
        and set first bin to 0.
        """
        if data == None or len(data) == 0: return data
        v = data[0]
        data += v
        data[0] -= v
        return data

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

    def transform(self, data, path):
        debug( "%s: called" % str(self))

        to_delete = set()
        first = True
        for key, values in data.iteritems():
            # first pair is bins - do not transform
            if first:
                first = False
                continue
            
            values = numpy.array( values, dtype = numpy.float )
            for converter in self.mConverters: values = converter(values)
            data[key] = values

        return data

########################################################################
########################################################################
########################################################################
class TransformerHistogram( TransformerAggregate ):
    '''compute a histograms of :term:`numerical arrays`.

    Example::

       Input:
       x=[ 1,1,1,1,1,2,2,2,4,4,5 ]
     
       Result (tf-bins=5]:
       x=[ 1.   1.8  2.6  3.4  4.2]
       frequency=[5,3,0,2,1]
     
    '''

    nlevels = 1

    options = Transformer.options +\
        ( ('tf-bins', directives.unchanged), 
          ('tf-range', directives.unchanged), 
          ('tf-max-bins', directives.unchanged),
          )

    def __init__(self, *args, **kwargs):
        TransformerAggregate.__init__(self, *args, **kwargs)

        self.mConverters = []
        self.mFormat = "%i"
        self.mBinMarker = "left"

        self.mBins = kwargs.get( "tf-bins", "100" )
        self.mRange = kwargs.get( "tf-range", None )
        self.max_bins = int(kwargs.get( "max-bins", "1000"))

        f = []
        if self.normalize_total in self.mConverters: f.append( "relative" )
        else: f.append( "absolute" )
        if self.cumulate in self.mConverters: f.append( "cumulative" )
        if self.reverse_cumulate in self.mConverters: f.append( "cumulative" )
        f.append("frequency")

        self.mYLabel = " ".join(f)

    def binToX( self, bins ):
        """convert bins to x-values."""
        if self.mBinMarker == "left": return bins[:-1]
        elif self.mBinMarker == "mean": 
            return [ (bins[x] - bins[x-1]) / 2.0 for x in range(1,len(bins)) ]
        elif self.mBbinMarker == "right": return bins[1:]

    def toHistogram( self, data ):
        '''compute the histogram.'''
        ndata = [ x for x in data if x != None and x != 'None' ]
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
                if ma < 0 or mi < 0: raise ValueError( "can not bin logarithmically for negative values.")
                if mi == 0: mi = numpy.MachAr().epsneg
                ma = numpy.log10( ma )
                mi = numpy.log10( mi )
                try:
                    bins = [ 10 ** x for x in arange( mi, ma, ma / nbins ) ]
                except ValueError, msg:
                    raise ValueError("can not compute %i bins for %f-%f: %s" % \
                                         (nbins, mi, ma, msg ) )
            elif binsize != None:
                # AH: why this sort statement? Removed
                # data.sort()

                # make sure that ma is part of bins
                bins = numpy.arange(mi, ma + binsize, binsize )
            else:
                try:
                    bins = eval(self.mBins)
                except SyntaxError, msg:
                    raise SyntaxError( "could not evaluate bins from `%s`, error=`%s`" \
                                           % (self.mBins, msg))


            if hasattr( bins, "__iter__"):
                if len(bins) == 0:
                    warn( "empty bins")
                    return None, None
                if self.max_bins > 0 and len(bins) > self.max_bins:
                    # truncate number of bins
                    warn( "too many bins (%i) - truncated to (%i)" % (len(bins), self.max_bins))
                    bins = self.max_bins

            # ignore histogram semantics warning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                hist, bin_edges = numpy.histogram( data, bins=bins, range=(mi,ma) )
        
        return self.binToX(bin_edges), hist

    def transform(self, data, path):
        debug( "%s: called for path %s" % (str(self), str(path)))

        to_delete = set()
        for header, values in data.iteritems():
            bins, values = self.toHistogram(values)
            if bins != None:
                for converter in self.mConverters: values = converter(values)
                data[header] =  odict( ((header, bins), ("frequency", values)))
            else:
                to_delete.add( header )

        for header in to_delete:
            del data[header]

        debug( "%s: completed for path %s" % (str(self), str(path)))
        return data
