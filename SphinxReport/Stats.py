import types
import math
import numpy
import scipy
import scipy.stats
import collections
try:
    from rpy import r as R
    import rpy
except ImportError:
    pass

def getSignificance( pvalue, thresholds=[0.05, 0.01, 0.001] ):
    """return cartoon of significance of a p-Value."""
    n = 0
    for x in thresholds:
        if pvalue > x: return "*" * n
        n += 1
    return "*" * n

#################################################################
#################################################################
#################################################################
## Perform log likelihood test
class LogLikelihoodTest:

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
        raise ValueError, "difference of degrees of freedom not larger than 0"
    
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
    """perform chi-squared test on a matrix."""
    nrows, ncols = matrix.shape
    if nrows != 2 or ncols != 2:
        raise "chi-square currently only implemented for 2x2 tables."

    df = (nrows - 1) * (ncols -1 )

    row_sums = [ sum(matrix[x,:]) for x in range( nrows ) ]
    col_sums = [ sum(matrix[:,x]) for x in range( ncols ) ]
    sample_size = sum(row_sums)

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

class DistributionalParameters:
    """a collection of distributional parameters. Available properties
    are:

    mMean, mMedian, mMin, mMax, mSampleStd, mSum, mCounts
    """
    def __init__(self, values = None, format = "%6.4f", mode="float"):

        self.mMean, self.mMedian, self.mMin, self.mMax, self.mSampleStd, self.mSum, self.mCounts, self.mQ1, self.mQ3 = \
                    (0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        if values != None and len(values) > 0: self.updateProperties( values )
        self.mFormat = format
        self.mMode = mode
        self.mNErrors = 0

    def updateProperties( self, values):
        """update properties.

        If values is an vector of strings, each entry will be converted
        to float. Entries that can not be converted are ignored.
        """
        values = [x for x in values if x != None ]

        if len(values) == 0:
            raise ValueError( "no data for statistics" )

        ## convert
        self.mNErrors = 0
        if type(values[0]) not in (types.IntType, types.FloatType):
            n = []
            for x in values:
                try:
                    n.append( float(x) )
                except ValueError:
                    self.mNErrors += 1
        else:
            n = values

        ## use a non-sort algorithm later.
        n.sort()
        self.mQ1 = n[len(n) / 4]
        self.mQ3 = n[len(n) * 3 / 4]
        
        self.mCounts = len(n)
        self.mMin = min(n)
        self.mMax = max(n)
        self.mMean = scipy.mean( n )
        self.mMedian = scipy.median( n )
        self.mSampleStd = scipy.std( n )
        self.mSum = reduce( lambda x, y: x+y, n )

    def getZScore( self, value ):
        """return zscore for value."""
        if self.mSampleStd > 0:
            return (value - self.mMean) / self.mSampleStd
        else:
            return 0

    def setFormat( self, format ):
        """set number format."""
        self.mFormat = format

    def getHeaders( self ):
        """returns header of column separated values."""
        return ("nval", "min", "max", "mean", "median", "stddev", "sum", "q1", "q3")

    def getHeader( self ):
        """returns header of column separated values."""
        return "\t".join( self.getHeaders())

    def items(self):
        return [ (x, self.__getitem__(x)) for x in self.getHeaders() ]

    def __getitem__( self, key ):
        
        if key == "nval": return self.mCounts
        if key == "min": return self.mMin
        if key == "max": return self.mMax
        if key == "mean": return self.mMean
        if key == "median": return self.mMedian
        if key == "stddev": return self.mSampleStd
        if key == "sum": return self.mSum
        if key == "q1": return self.mQ1
        if key == "q3": return self.mQ3                

        raise KeyError, key
        
    def __str__( self ):
        """return string representation of data."""
        
        if self.mMode == "int":
            format_vals = "%i"
            format_median = "%.1f"
        else:
            format_vals = self.mFormat
            format_median = self.mFormat

        return "\t".join( ( "%i" % self.mCounts,
                            format_vals % self.mMin,
                            format_vals % self.mMax,
                            self.mFormat % self.mMean,
                            format_median % self.mMedian,
                            self.mFormat % self.mSampleStd,                                      
                            format_vals % self.mSum,
                            format_vals % self.mQ1,
                            format_vals % self.mQ3,                            
                            ) )

class Summary(DistributionalParameters):
    """a shorter name for DistributionalParameters
    """
    pass


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
class CorrelationTest:
    def __init__(self, 
                 r_result = None, 
                 s_result = None,
                 method = None):
        self.mPValue = None
        self.mMethod = None

        if r_result:
            self.mCoefficient = r_result['estimate']['cor']
            self.mPValue = float(r_result['p.value'])
            self.mNObservations = r_result['parameter']['df']
            self.mMethod = r_result['method']
            self.mAlternative = r_result['alternative']
        elif s_result:
            self.mCoefficient = s_result[0]
            self.mPValue = s_result[1]
            self.mNObservations = 0
            self.mAlternative = "two-sided"

        if method: self.mMethod = method

        if self.mPValue != None:
            self.mSignificance = getSignificance( self.mPValue )

    def __str__(self):
        return "\t".join( (
            "%6.4f" % self.mCoefficient,
            "%e" % self.mPValue,
            self.mSignificance,
            "%i" % self.mNObservations,
            self.mMethod,
            self.mAlternative ) )
    def getHeaders(self):
        return ("coeff", "pvalue", "significance", "observations", "method", "alternative" )
    
def filterMasked( xvals, yvals, missing = ("na", "Nan", None, ""), dtype = numpy.float ):
    """convert xvals and yvals to numpy array skipping pairs with
    one or more missing values."""
    xmask = [ i in missing for i in xvals ]
    ymask = [ i in missing for i in yvals ]
    return (numpy.array( [xvals[i] for i in range(len(xvals)) if not xmask[i]], dtype = dtype  ),
            numpy.array( [yvals[i] for i in range(len(yvals)) if not ymask[i]], dtype = dtype) )

def doCorrelationTest( xvals, yvals ):
    """compute correlation between x and y.

    Raises a value-error if there are not enough observations.
    """

    if len(xvals) <= 1 or len(yvals) <= 1:
        raise ValueError( "can not compute correlation with no data" )
    if len(xvals) != len(yvals):
        raise ValueError( "data vectors have unequal length" )
    
#     try:
#         result = CorrelationTest( r_result = R.cor_test( xvals, yvals, na_action="na_omit" ) )
#     except rpy.RPyException, msg:
#         raise ValueError( msg )

    x, y = filterMasked( xvals, yvals )

    result = CorrelationTest( s_result = scipy.stats.pearsonr( x, y ),
                              method = "pearson" )
    result.mNObservations = len(x)

    return result


 
