import types
import math
import numpy

import scipy
from functools import reduce
# See http://projects.scipy.org/scipy/ticket/1739
# scipy 0.11 for python3 broken, should be fixed for scipy 0.12
try: import scipy.stats
except ValueError: scipy.stats = None

import collections, itertools

try:
    from rpy2.robjects import r as R
    import rpy2.robjects as ro
    import rpy2.robjects.numpy2ri
except ImportError:
    R = None

from collections import OrderedDict as odict

def getSignificance( pvalue, thresholds=[0.05, 0.01, 0.001] ):
    """return cartoon of significance of a p-Value."""
    n = 0
    for x in thresholds:
        if pvalue > x: return "*" * n
        n += 1
    return "*" * n

class Result(object):
    '''allow both member and dictionary access.'''
    slots=("_data")
    def __init__(self):
        object.__setattr__(self, "_data", odict())
    def fromR( self, take, r_result ):
        '''convert from an *r_result* dictionary using map *take*.

        *take* is a list of tuples mapping a field to the corresponding
        field in *r_result*.
        '''
        for x,y in take:
            if y:
                self._data[x] = r_result.rx(y)[0][0]
            else:
                self._data[x] = r_result.rx(x)[0][0]

        return self
    def __len__(self): return self._data.__len__()
    def __getattr__(self, key):
        if not key.startswith("_"):
            try: return object.__getattribute__(self,"_data")[key]
            except KeyError: pass
        return getattr( self._data, key )
    def keys(self): return list(self._data.keys())
    def values(self): return list(self._data.values())
    def __iter__(self): return self._data.__iter__()
    def __str__(self):
        return str(self._data)
    def __contains__(self,key):
        return key in self._data
    def __getitem__(self, key ):
        return self._data[key]
    def __delitem__(self, key ):
        del self._data[key]
    def __setitem__(self, key, value ):
        self._data[key] = value
    def __setattr__(self, key, value):
        if not key.startswith("_"):
            self._data[key] = value
        else:
            object.__setattr__(self,key,value)
    def __getstate__(self):
        # required for correct pickling/unpickling
        return object.__getattribute__(self,"_data")
            
    def __setstate__(self,d):
        # required for correct unpickling, otherwise
        # maximum recursion threshold will be reached
        object.__setattr__(self, "_data", d)

#################################################################
#################################################################
#################################################################
## Perform log likelihood test
class LogLikelihoodTest(Result):

    def __init__(self):
        pass

def doLogLikelihoodTest( complex_ll, complex_np,
                         simple_ll, simple_np,
                         significance_threshold = 0.05):
    """perform log-likelihood test between model1 and model2.
    """

    assert complex_ll >= simple_ll, "log likelihood of complex model smaller than for simple model: %f > %f" % (complex_ll, simple_ll)

    chi = 2 * (complex_ll - simple_ll)
    df = complex_np - simple_np

    if df <= 0:
        raise ValueError("difference of degrees of freedom not larger than 0")
    
    p = scipy.stats.chisqprob( chi, df )
    
    l = LogLikelihoodTest()
    
    l.mComplexLogLikelihood = complex_ll
    l.mSimpleLogLikelihood = simple_ll    
    l.mComplexNumParameters = complex_np
    l.mSimpleNumParameters = simple_np    
    l.mSignificanceThreshold = significance_threshold
    l.mProbability = p
    l.mChiSquaredValue = chi
    l.mDegreesFreedom = df

    if p < significance_threshold:
        l.mPassed = True
    else:
        l.mPassed = False
        
    return l

#################################################################
#################################################################
#################################################################
class BinomialTest:
    def __init__(self):
        pass

def doBinomialTest( p, sample_size, observed, significance_threshold = 0.05):
    """perform a binomial test. 
    
    Given are p: the probability of the NULL hypothesis, the sample_size
    and the number of observed counts.
    """
    pass

#################################################################
#################################################################
#################################################################
class ChiSquaredTest:
    def __init__(self):
        pass

def doChiSquaredTest( matrix, significance_threshold = 0.05 ):
    """perform chi-squared test on a matrix.
    """
    nrows, ncols = matrix.shape
    if nrows != 2 or ncols != 2:
        raise ValueError("chi-square currently only implemented for 2x2 tables.")

    df = (nrows - 1) * (ncols -1 )

    row_sums = [ matrix[x,:].sum() for x in range( nrows ) ]
    col_sums = [ matrix[:,x].sum() for x in range( ncols ) ]
    sample_size = float( sum(row_sums) )

    chi = 0.0
    for x in range(nrows):
        for y in range(ncols):
            expected = row_sums[x] * col_sums[y] / sample_size
            d = matrix[x,y] - expected
            chi += d * d / expected

    result = ChiSquaredTest()

    result.mProbability = scipy.stats.chisqprob( chi, df )
    result.mDegreesFreedom = df
    result.mChiSquaredValue = chi
    result.mPassed = result.mProbability < significance_threshold
    result.mSignificance = getSignificance( result.mProbability )
    result.mSampleSize = sample_size
    result.mPhi = math.sqrt( result.mChiSquaredValue / result.mSampleSize )
    return result

def doPearsonChiSquaredTest( p, sample_size, observed, significance_threshold = 0.05):
    """perform a pearson chi squared test.
    
    Given are p: the probability of the NULL hypothesis, the sample_size
    and the number of observed counts.
    
    For large sample sizes, this test is a continuous approximation to
    the binomial test.
    """
    e = float(p) * sample_size
    d = float(observed) - e
    chi = d * d / e
    df = 1

    result = ChiSquaredTest()

    result.mProbability = scipy.stats.chisqprob( chi, df )
    result.mDegreesFreedom = df
    result.mChiSquaredValue = chi
    result.mPassed = result.mProbability < significance_threshold
    result.mSignificance = getSignificance( result.mProbability )
    result.mSampleSize = sample_size
    result.mPhi = math.sqrt( result.mChiSquaredValue / result.mSampleSize )
    result.mObserved = observed
    result.mExpected = e
    return result

#################################################################
#################################################################
#################################################################
## Convenience functions and objects for statistical analysis

class Summary( Result ):
    """a collection of distributional parameters. Available properties
    are:

    mean, median, min, max, samplestd, sum, counts
    """
    def __init__(self, values = None, format = "%6.4f", mode="float" ):
        Result.__init__(self)
        self._format = format
        self._mode = mode
        # note that this determintes the order of the fields at output
        self.counts, self.min, self.max, self.mean, self.median, self.samplestd, self.sum, self.q1, self.q3 = \
                    (0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        if values != None:

            values = [x for x in values if x != None ]

            if len(values) == 0:
                raise ValueError( "no data for statistics" )

            # convert
            self._nerrors = 0
            if type(values[0]) not in (int, float):
                n = []
                for x in values:
                    try:
                        n.append( float(x) )
                    except ValueError:
                        self._nerrors += 1
            else:
                n = values

            if len(n) == 0:
                raise ValueError( "no data for statistics" )

            ## use a non-sort algorithm later.
            n.sort()
            self.q1 = n[len(n) / 4]
            self.q3 = n[len(n) * 3 / 4]

            self.counts = len(n)
            self.min = min(n)
            self.max = max(n)
            self.mean = numpy.mean( n )
            self.median = numpy.median( n )
            self.samplestd = numpy.std( n )
            self.sum = reduce( lambda x, y: x+y, n )

    def getHeaders( self ):
        """returns header of column separated values."""
        return ("nval", "min", "max", "mean", "median", "stddev", "sum", "q1", "q3")

    def getHeader( self ):
        """returns header of column separated values."""
        return "\t".join( self.getHeaders())

    def __str__( self ):
        """return string representation of data."""
        
        if self._mode == "int":
            format_vals = "%i"
            format_median = "%.1f"
        else:
            format_vals = self._format
            format_median = self._format

        return "\t".join( ( "%i" % self.counts,
                            format_vals % self.min,
                            format_vals % self.max,
                            self._format % self.mean,
                            format_median % self.median,
                            self._format % self.samplestd,                                      
                            format_vals % self.sum,
                            format_vals % self.q1,
                            format_vals % self.q3,                            
                            ) )

class FDRResult:
    def __init__(self):
        pass

    def plot(self, hardcopy = None):

        if hardcopy:
            R.png(hardcopy, width=1024, height=768, type="cairo")

        R.require('qvalue')

        # build a qobj
        R.assign( "pval", self.mPValues )
        R.assign( "pi0", self.mPi0 )
        R.assign( "qval", self.mQValues )
        R.assign( "lambda", self.mLambda )
        R("""qobj <-list( pi0=pi0, qvalues=qval, pvalues=pval, lambda=lambda)""")
        R(""" class(qobj) <- "qvalue" """)

        R("""qplot(qobj)""")

        if hardcopy:
            R.dev_off()

def doFDR(pvalues, 
          vlambda=numpy.arange(0,0.95,0.05), 
          pi0_method="smoother", 
          fdr_level=None, 
          robust=False,
          smooth_df = 3,
          smooth_log_pi0 = False):
    """modeled after code taken from http://genomics.princeton.edu/storeylab/qvalue/linux.html.

    I did not like the error handling so I translated most to python.
    """

    if min(pvalues) < 0 or max(pvalues) > 1:
        raise ValueError( "p-values out of range" )

    if len(vlambda) > 1 and len(vlambda) < 4:
        raise ValueError(" If length of vlambda greater than 1, you need at least 4 values." )

    if len(vlambda) > 1 and (min(vlambda) < 0 or max(vlambda) >= 1):
        raise ValueError( "vlambda must be within [0, 1).")

    m = len(pvalues)

     # these next few functions are the various ways to estimate pi0
    if len(vlambda)==1: 
        vlambda = vlambda[0]
        if  vlambda < 0 or vlambda >=1 :
            raise ValueError( "vlambda must be within [0, 1).")

        pi0 = numpy.mean( [ x >= vlambda for x in pvalues ] ) / (1.0 - vlambda)
        pi0 = min(pi0, 1.0)
        R.assign( "pi0", pi0)
    else:
        pi0 = numpy.zeros( len(vlambda), numpy.float )

        for i in range( len(vlambda) ):
            pi0[i] = numpy.mean( [x >= vlambda[i] for x in pvalues ]) / (1.0 -vlambda[i] )

        R.assign( "pi0", pi0)
        R.assign( "vlambda", vlambda)

        if pi0_method=="smoother":
            if smooth_log_pi0:
                pi0 = math.log(pi0)
                
            R.assign( "smooth_df", smooth_df)

            spi0 = R("""spi0 <- smooth.spline(vlambda,pi0, df = smooth_df)""")
            pi0 = R("""pi0 <- predict( spi0, x = max(vlambda) )$y""")

            if smooth_log_pi0:
                pi0 = math.exp(pi0)

        elif pi0_method=="bootstrap":

            minpi0 = min(pi0)

            mse = numpy.zeros( len(vlambda), numpy.float )
            pi0_boot = numpy.zeros( len(vlambda), numpy.float )

            R.assign( "pvalues", pvalues)
            pi0 = R("""
            m <- length(pvalues)
            minpi0 <- min(pi0)
            mse <- rep(0,length(vlambda))
            pi0_boot <- rep(0,length(vlambda))
            for(i in 1:100) 
            {
                pvalues_boot <- sample(pvalues,size=m,replace=TRUE)
                for(i in 1:length(vlambda)) 
                {
                    pi0_boot[i] <- mean(pvalues_boot>vlambda[i])/(1-vlambda[i])
                }
                mse <- mse + (pi0_boot-minpi0)^2
            }
            pi0 <- min(pi0[mse==min(mse)])""")
        else:
            raise ValueError( "'pi0_method' must be one of 'smoother' or 'bootstrap'.")

        pi0 = min(pi0,1.0)

    if pi0 <= 0:
        raise ValueError( "The estimated pi0 <= 0. Check that you have valid p-values or use another vlambda method." )

    if fdr_level != None and (fdr_level <= 0 or fdr_level > 1):
        raise ValueError( "'fdr_level' must be within (0, 1].")

    # The estimated q-values calculated here
    #u = numpy.argsort( p )

    # change by Alan
    # ranking function which returns number of observations less than or equal
    R.assign( "pvalues", pvalues )
    R.assign( "robust", robust )
    qvalues = R("""u <- order(pvalues)
    qvalues.rank <- function(x) 
{
      idx <- sort.list(x)

      fc <- factor(x)
      nl <- length(levels(fc))
      bin <- as.integer(fc)
      tbl <- tabulate(bin)
      cs <- cumsum(tbl)

      tbl <- rep(cs, tbl)
      tbl[idx] <- tbl

      return(tbl)
}

v <- qvalues.rank(pvalues)
m <- length(pvalues)

qvalues <- pi0 * m * pvalues / v
if(robust) 
{
        qvalues <- pi0*m*pvalues/(v*(1-(1-pvalues)^m))
}
qvalues[u[m]] <- min(qvalues[u[m]],1)
for(i in (m-1):1) 
{
   qvalues[u[i]] <- min(qvalues[u[i]],qvalues[u[i+1]],1)
}
qvalues
""")

    result = FDRResult()
    result.mQValues = qvalues

    if fdr_level != None:
        result.mPassed = [ x <= fdr_level for x in result.mQValues ]

    result.mPValues = pvalues
    result.mPi0 = pi0
    result.mLambda = vlambda
    
    return result

#################################################################
#################################################################
#################################################################
class CorrelationTest(Result):
    def __init__(self, 
                 r_result = None, 
                 s_result = None,
                 method = None,
                 nobservations = 0):
        Result.__init__(self)

        self.pvalue = None
        self.method = method
        self.nobservations = 0

        if r_result:
            self.coefficient = r_result['estimate']['cor']
            self.pvalue = float(r_result['p.value'])
            self.nobservations = r_result['parameter']['df']
            self.method = r_result['method']
            self.alternative = r_result['alternative']
        elif s_result:
            self.coefficient = s_result[0]
            self.pvalue = s_result[1]
            self.nobservations = nobservations
            self.alternative = "two-sided"
            
        if self.pvalue != None:
            if self.pvalue > 0:
                self.logpvalue = math.log( self.pvalue )
            else:
                self.logpvalue = 0
            self.significance = getSignificance( self.pvalue )

    def __str__(self):
        return "\t".join( (
            "%6.4f" % self.coefficient,
            "%e" % self.pvalue,
            self.significance,
            "%i" % self.nobservations,
            self.method,
            self.alternative ) )

def filterMasked( xvals, yvals, missing = ("na", "Nan", None, ""), dtype = numpy.float ):
    """convert xvals and yvals to numpy array skipping pairs with
    one or more missing values."""
    xmask = [ i in missing for i in xvals ]
    ymask = [ i in missing for i in yvals ]
    return (numpy.array( [xvals[i] for i in range(len(xvals)) if not xmask[i]], dtype = dtype  ),
            numpy.array( [yvals[i] for i in range(len(yvals)) if not ymask[i]], dtype = dtype) )

def filterNone( args, missing = ("na", "Nan", None, "", 'None', 'none'), dtype = numpy.float ):
    '''convert arrays in 'args' to numpy arrays of 'dtype', skipping where any of
    the columns have a value of missing.

    >>> Stats.filterNone( ((1,2,3), (4,5,6)) )
    [array([ 1.,  2.,  3.]), array([ 4.,  5.,  6.])]
    >>> Stats.filterNone( ((1,2,3), (4,None,6)) )
    [array([ 1.,  3.]), array([ 4.,  6.])]
    >>> Stats.filterNone( ((None,2,3), (4,None,6)) )
    [array([ 3.]), array([ 6.])]
    '''
    mi = min([len(x) for x in args])
    ma = max([len(x) for x in args])
    assert mi == ma, "arrays have unequal length to start with: min=%i, max=%i." % (mi,ma)
    
    mask = [ sum( [z in missing for z in x] ) for x in zip(*args) ]

    return [ numpy.array( [x[i] for i in range(len(x)) if not mask[i]], dtype = dtype) for x in args ]

def doCorrelationTest( xvals, yvals, method = "pearson" ):
    """compute correlation between x and y.

    Raises a value-error if there are not enough observations.
    """

    if scipy.stats == None:
        raise ImportError("scipy.stats not available")

    if len(xvals) <= 1 or len(yvals) <= 1:
        raise ValueError( "can not compute correlation with no data" )
    if len(xvals) != len(yvals):
        raise ValueError( "data vectors have unequal length" )
    
#     try:
#         result = CorrelationTest( r_result = R.cor_test( xvals, yvals, na_action="na_omit" ) )
#     except rpy.RPyException, msg:
#         raise ValueError( msg )

    x, y = filterMasked( xvals, yvals )


    if method == "pearson":
        s_result = scipy.stats.pearsonr( x, y )
    elif method == "spearman":
        s_result = scipy.stats.spearmanr( x, y )
    else:
        raise ValueError("unknown method %s" % (method))

    result = CorrelationTest( s_result = s_result,
                              method = method,
                              nobservations = len(x))

    return result


###################################################################
###################################################################
###################################################################
## compute ROC curves from sorted values
###################################################################
def computeROC( values ):
    '''return a roc curve for *values*.
    Values is a sorted list of (value, bool) pairs.

    '''
    roc = []
    
    npositives = len( [x for x in values if x[1] ] )
    if npositives == 0: 
        raise ValueError( "no positives among values" )

    ntotal = len(values)

    last_value, last_fpr = None, None
    tp, fp = 0, 0
    tn, fn = ntotal - npositives, npositives 

    for value, is_positive in values:
        if is_positive: 
            tp += 1
            fn -= 1
        else: 
            fp += 1
            tn -= 1

        if last_value != value:

            try:
                tpr = float(tp) / (tp + fn)
            except ZeroDivisionError:
                tpr = 0

            try:
                fpr = float(fp) / (fp + tn)
            except ZeroDivisionError:
                fpr = 0
                
            if last_fpr != fpr:
                roc.append( (fpr,tpr) )
                last_fpr = fpr

        last_values = value

    return roc

###################################################################
###################################################################
###################################################################
## 
###################################################################
def getAreaUnderCurve( xvalues, yvalues ):
    '''compute area under curve from a set of discrete x,y coordinates
    using trapezoids.
    
    This is only as accurate as the density of points.
    '''

    assert len(xvalues) == len(yvalues)
    last_x, last_y = xvalues[0], yvalues[0]
    auc = 0
    for x,y in zip(xvalues, yvalues)[1:]:
        dx = x - last_x
        assert not dx < 0, "x not increasing: %f >= %f" % (last_x, x)
        dy = abs(last_y - y)
        my = min(last_y, y)
        # rectangle plus triangle
        auc += dx * my + dx * dy / 2
        last_x, last_y = x, y
        
    return auc

###################################################################
###################################################################
###################################################################
## 
###################################################################
def getSensitivityRecall( values ):
    '''return sensitivity/selectivity.

    Values is a sorted list of (value, bool) pairs.
    '''

    npositives = 0.0
    npredicted = 0.0
    l = None
    result = []
    total = float(len(values))
    for value, is_positive in values:
        npredicted += 1.0
        if is_positive > 0: npositives += 1.0
        if value != l:
            result.append( (value, npositives / npredicted, npredicted / total ) )
        l = value
    if l:
        result.append( (l, npositives / npredicted, npredicted/total ) )

    return result

###################################################################
###################################################################
###################################################################
## 
###################################################################
def doMannWhitneyUTest( xvals, yvals ):
    '''apply the Mann-Whitney U test to test for the difference of medians.'''


    r_result = R['wilcox.test']( xvals, yvals, paired = False )

    result = Result().fromR( 
        ( ("pvalue", 'p.value'),
          ('alternative', None),
          ('method', None ) ), 
        r_result )

    return result

