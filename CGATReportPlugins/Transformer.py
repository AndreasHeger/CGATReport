import itertools
import numpy
import pandas
import math

# used in evals for computing bins in histograms
from numpy import arange

from collections import OrderedDict as odict
from CGATReport.Component import Component
from CGATReport import Stats, DataTree, Utils

from docutils.parsers.rst import directives

# for rpy2 for data frames
try:
    import rpy2
    from rpy2.robjects import r as R
except ImportError:
    R = None

# ignore numpy histogram warnings in versions 1.3
import warnings


class Transformer(Component):

    '''Base class for transformers.

    Implements the basic __call__ method that iterates over
    a:term:`data tree` and calls self.transform method on the
    appropriate levels in the hierarchy.

    The property nlevels determines the grouping within a
    Transformer. If it is set to 0, data will be grouped by all
    levels in the index. If nlevels is None, the dataframe will not be
    grouped. If nlevels it is a positive number, a certain number of
    levels will be ignored from grouping.

    If nlevels is a positive number, the first nlevel levels will not
    be grouped. If it is a negative numbers, the last nlevel levels
    will be ignored for groupning.

    '''

    capabilities = ['transform']

    nlevels = None

    # If true, prune index in dataframe to
    # same levels as input
    prune_dataframe = True

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)

    def __call__(self, data):

        if self.nlevels is None:
            # do not group
            return self.transform(data)

        dataframes, keys = [], []
        group_levels = Utils.getGroupLevels(
            data,
            modify_levels=self.nlevels,
        )

        for key, group in data.groupby(level=group_levels):
            self.debug('applying transformation on group %s' % str(key))
            df = self.transform(group)
            if df is not None:
                dataframes.append(df)
                keys.append(key)

        df = pandas.concat(dataframes, keys=keys)
        
        if self.prune_dataframe:
            # reset dataframe index - keep the same levels
            Utils.pruneDataFrameIndex(df, original=data)

        self.debug("transform: finished")

        return df


########################################################################
########################################################################
# Conversion transformers
########################################################################
########################################################################
# class TransformerToLabels(Transformer):

#     '''convert:term:`numerical arrays` to:term:`labeled data`.

#     By default, the items are labeled numerically. If `tf-labels`
#     is given it is used instead.

#     Example::

#        Input:                 Returns:
#        a/keys/['x','y','z']   a/x/1
#        a/values/[4,5,6]       a/y/2
#                               a/z/3

#     Or::
#        Input:                       Returns:
#        a/contigs/['chr1','chr2']    a/chr1/10
#        a/lengths/[10,20]            a/chr2/20

#     Note that the outcome is equivalent to a pivot.

#     '''
#     nlevels = 1

#     options = Transformer.options +\
#         (('tf-labels', directives.unchanged),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         self.labels = kwargs.get("tf-labels", None)

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         if len(data) == 0:
#             return data

#         keys = list(data.keys())
#         # pairs of data, see use case 2
#         if len(keys) == 2:
#             return odict(zip(*data.values()))

#         if self.labels:
#             labels = data[self.labels]
#             del keys[keys.index(self.labels)]
#             if len(keys) < 1:
#                 raise ValueError("TransformerToLabels requires at "
#                                  "least two arrays, got only 1, "
#                                  "if tf-labels is set")
#         else:
#             max_nkeys = max([len(x) for x in list(data.values())])
#             labels = list(range(1, max_nkeys + 1))

#         labels = list(map(str, labels))

#         if len(data) == 2:
#             new_data = odict(list(zip(labels, data[keys[0]])))
#         else:
#             new_data = odict()
#             for key in keys:
#                 new_data[key] = odict(list(zip(labels, data[key])))

#         return new_data


# class TransformerToList(Transformer):

#     '''transform categorized data into lists.

#     Example::

#        Input:            Returns:
#        a/x/1             x/[1,4]
#        a/y/2             y/[2,5]
#        a/z/3             z/[3,6]
#        b/x/4
#        b/y/5
#        b/z/6

#     '''
#     nlevels = 2

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         lists = odict()

#         for major_key, values in data.items():
#             for minor_key, value in values.items():
#                 if minor_key in lists:
#                     lists[minor_key].append(value)
#                 else:
#                     lists[minor_key] = [value]

#         sizes = [len(x) for x in list(lists.values())]
#         if max(sizes) != min(sizes):
#             warn("%s: list of unequal sizes: min=%i, max=%i" %
#                  (self, min(sizes), max(sizes)))
#         return lists

# ########################################################################
# ########################################################################
# ########################################################################


# class TransformerToRDataFrame(Transformer):

#     '''transform data into one or more data frames.

#     Example::

#        Input:                                Output:
#        experiment1/expression = [1,2,3]      experiment1/df({ expression: [1,2,3], counts: [3,4,5] })
#        experiment1/counts = [3,4,5]          experiment2/df({ expression: [8,9,1], counts: [4,5,6] })
#        experiment2/expression = [8,9,1]
#        experiment2/counts = [4,5,6]

#     '''
#     nlevels = 1

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         t = odict()
#         for minor_key, values in data.items():
#             if not Utils.isArray(values):
#                 raise ValueError("expected a list for data frame "
#                                  "creation, got %s", type(data))
#             if len(values) == 0:
#                 raise ValueError("empty list for %s" % (minor_key))
#             v = values[0]
#             if Utils.isInt(v):
#                 t[minor_key] = rpy2.robjects.IntVector(values)
#             elif Utils.isFloat(v):
#                 t[minor_key] = rpy2.robjects.FloatVector(values)
#             else:
#                 t[minor_key] = rpy2.robjects.StrVector(values)
 
#         return rpy2.robjects.DataFrame(t)


# class TransformerToDataFrame(Transformer):

#     '''transform data into one or more data frames.

#     Example::

#        Input:                                Output:
#        experiment1/expression = [1,2,3]      experiment1/df({ expression: [1,2,3], counts: [3,4,5] })
#        experiment1/counts = [3,4,5]          experiment2/df({ expression: [8,9,1], counts: [4,5,6] })
#        experiment2/expression = [8,9,1]
#        experiment2/counts = [4,5,6]

#     '''

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#     def __call__(self, data):

#         result = DataTree.asDataFrame(data)
#         return odict((('all', result),))


# class TransformerIndicator(Transformer):

#     '''take a field from the lowest level and
#     build an absent/present indicator out of it.
#     '''

#     nlevels = 1
#     default = 0

#     options = Transformer.options +\
#         (('tf-fields', directives.unchanged),
#          ('tf-level', directives.length_or_unitless))

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         raise NotImplementedError('transformer indicator is not implemented')
#         try:
#             self.filter = kwargs["tf-fields"]
#         except KeyError:
#             raise KeyError("TransformerIndicator requires the "
#                            "`tf-fields` option to be set.")

#         try:
#             self.nlevels = int(kwargs["tf-level"])
#         except KeyError:
#             pass

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         vals = data[self.filter]
#         return odict(list(zip(vals, [1] * len(vals))))


# class TransformerCount(Transformer):

#     '''compute counts of values in the hierarchy.

#     Displaying a table of counts can often be useful to
#     summarize the number of entries in a list prior to
#     plotting.

#     The following operations are perform when:term:`tf-level` is set
#     to ``1``::
#        Input:          Returns:
#        a/x=[1,2,3]            a/x=3
#        a/y=[1,3,5]            a/y=3
#        b/x=[34,3]             b/x=2
#        b/y=[2,4]              b/y=2
#     '''

#     nlevels = 1
#     default = 0

#     options = Transformer.options +\
#         (('tf-level', directives.length_or_unitless),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         try:
#             self.nlevels = int(kwargs["tf-level"])
#         except KeyError:
#             pass

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         for v in list(data.keys()):
#             data[v] = len(data[v])

#         return data

########################################################################
########################################################################
# Filtering transformers
########################################################################
########################################################################
class TransformerPandas(Transformer):
    '''apply pandas dataframe methods to dataframe.

    '''

    nlevels = None
    default = 0

    options = Transformer.options +\
        (('tf-statement', directives.unchanged),)

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        try:
            self.statement = kwargs["tf-statement"]
        except KeyError:
            raise KeyError("TransformerPandas requires the "
                           "`tf-statement` option to be set.")

    def transform(self, data):
        exec "data = data.{}".format(self.statement)
        return data


class TransformerFilter(Transformer):
    '''select columns from a dataframe.

    The columns are specified in the ``tf-fields`` option.

    '''

    nlevels = None
    default = 0

    options = Transformer.options +\
        (('tf-fields', directives.unchanged),)

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        try:
            self.filter = kwargs["tf-fields"].split(",")
        except KeyError:
            raise KeyError("TransformerFilter requires the "
                           "`tf-fields` option to be set.")

    def transform(self, data):
        self.debug("%s: called" % str(self))
        return data[self.filter]


# class TransformerSelect(Transformer):

#     '''replace the lowest hierarchy with a single value.

#     This transformer removes all branches in a:term:`data tree` on
#     level:term:`tf-level` that do not match the :term:`tf-fields`
#     option.

#     The following operations are perform when:term:`tf-fields` is set
#     to ``x``::

#        Input:          Returns:
#        a/x=1            a=1
#        a/y=2            b=3
#        b/x=3
#        b/y=4

#     '''

#     nlevels = None
#     default = 0

#     options = Transformer.options +\
#         (('tf-fields', directives.unchanged),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         try:
#             self.fields = kwargs["tf-fields"].split(",")
#         except KeyError:
#             raise KeyError("TransformerSelect requires the "
#                            "`tf-fields` option to be set.")

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         nfound = 0
#         for v in list(data.keys()):
#             for field in self.fields:
#                 try:
#                     data[v] = data[v][field]
#                     nfound += 1
#                     break
#                 except KeyError:
#                     pass
#             else:
#                 data[v] = self.default

#         if nfound == 0:
#             raise ValueError("could not find any field "
#                              "from `%s` in %s" %
#                              (str(self.fields), path))

#         return data


# class TransformerSwop(Transformer):

#     '''swop two levels in the data tree.

#     For example:

#     track1/gene_id=1, track1/gene_name=1
#     track2/gene_id=1, track2/gene_name=2

#     with tf-swop=0,1

#     will become:

#     '''
#     options = Transformer.options +\
#         (('tf-fields', directives.unchanged),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         try:
#             self.fields = kwargs["tf-fields"].split(",")
#         except KeyError:
#             raise KeyError("TransformerGroup requires the "
#                            "`tf-fields` option to be set.")

#         if len(self.fields) != 2:
#             raise ValueError("`tf-fields` requires exactly "
#                              "two fields for swapping")

#         self.fields = map(int, self.fields)

#     def __call__(self, data):
#         return DataTree.swop(data, self.fields[0], self.fields[1])


# class TransformerGroup(Transformer):

#     '''group second-to-last level by lowest level.

#     For example:

#     track1/gene_id=1, track1/gene_name=1
#     track2/gene_id=1, track2/gene_name=2

#     with tf-fields=gene_id

#     will become:

#     gene_id1/gene_name=1
#     gene_id1/tracks = [track1,track2]

#     Note that other fields not in the group field will take the value
#     of the first row.

#     For example::

#        Input:    Output:
#        a/x=1     x/y=1
#        a/y=1     x/tracks[a,b]
#        b/x=1
#        b/y=2

#     '''

#     nlevels = 2
#     default = 0

#     options = Transformer.options +\
#         (('tf-fields', directives.unchanged),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         try:
#             self.fields = kwargs["tf-fields"].split(",")
#         except KeyError:
#             raise KeyError("TransformerGroup requires the "
#                            "`tf-fields` option to be set.")

#         if len(self.fields) != 1:
#             raise ValueError("`tf-fields` requires exactly "
#                              "one field for grouping function")

#         self.field = self.fields[0]

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         new_data = odict()

#         for v in list(data.keys()):
#             other_fields = [x for x in list(data[v].keys())
#                             if x != self.field]
#             for pos, val in enumerate(data[v][self.field]):
#                 if val not in new_data:
#                     new_data[val] = odict()
#                 if "group" not in new_data[val]:
#                     for o in other_fields:
#                         new_data[val][o] = data[v][o][pos]
#                     new_data[val]["group"] = ""
#                 new_data[val]["group"] += ",%s" % v

#         return new_data


# class TransformerCombinations(Transformer):

#     '''build combinations.

#     Level=2 can be used for labeled data::

#        Input:      Output:
#        a/x=1       a x b/a/x=1
#        b/x=2       a x b/b/x=2
#        c/x=3       a x c/a/x=1
#                    a x c/b/x=2
#                    b x c/a/x=2
#                    b x c/a/x=3

#     Uses the ``tf-fields`` option to combine a certain field.
#     Otherwise, it combines the first data found.

#     level=1 is useful to combine lists::

#        Input:            Output:
#        a/data=[1,2,3]    a x b/a=[1,2,3]
#        b/data=[2,4,5]    a x b/b=[2,4,5]
#        c/data=[4,2,1]    a x c/a=[1,2,3]
#                          a x c/a=[4,2,1]
#                          b x c/a=[2,4,5]
#                          b x c/a=[4,2,1]

#     '''

#     nlevels = 2

#     options = Transformer.options +\
#         (('tf-level', directives.length_or_unitless),
#          ('tf-fields', directives.unchanged),)

#     def __init__(self, *args, **kwargs):
#         Transformer.__init__(self, *args, **kwargs)

#         try:
#             self.fields = set(kwargs["tf-fields"].split(","))
#         except KeyError:
#             self.fields = None

#         self.nlevels = int(kwargs.get("tf-level", self.nlevels))

#     def transform(self, data, path):
#         self.debug("%s: called" % str(self))

#         vals = list(data.keys())
#         new_data = odict()

#         for x1 in range(len(vals) - 1):
#             n1 = vals[x1]
#             # find the first field that fits
#             if self.fields:
#                 for field in self.fields:
#                     if field in data[n1]:
#                         d1 = data[n1][field]
#                         break
#                 else:
#                     raise KeyError("could not find any match "
#                                    "from '%s' in '%s'" %
#                                    (str(list(data[n1].keys())),
#                                     str(self.fields)))
#             else:
#                 d1 = data[n1]

#             for x2 in range(x1 + 1, len(vals)):
#                 n2 = vals[x2]
#                 if self.fields:
#                     try:
#                         d2 = data[n2][field]
#                     except KeyErrror:
#                         raise KeyError("no field %s in '%s'" % sttr(data[n2]))
#                 else:
#                     d2 = data[n2]

#                 DataTree.setLeaf(new_data,
#                                  (("%s x %s" % (n1, n2)), n1),
#                                  d1)

#                 DataTree.setLeaf(new_data,
#                                  (("%s x %s" % (n1, n2)), n2),
#                                  d2)

#         return new_data


class TransformerStats(Transformer):
    '''Compute summary statistics for each
    column in a table.

    The summary statistics will be the columns
    of the data frame, while the column headers
    will be in the rows.
    '''

    # make sure that at least one grouping is done.
    nlevels = -1

    # keep row names (samples)
    prune_dataframe = False

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

    def transform(self, data):
        self.debug("%s: called" % str(self))
        return data.describe().transpose()


class TransformerHistogramStats(Transformer):

    # make sure that at least one grouping is done.
    nlevels = -1

    # keep row names (samples)
    prune_dataframe = False

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

    def transform(self, data):
        self.debug("%s: called" % str(self))
        if len(data.columns) < 2:
            raise ValueError("expected at least two columns")
        
        bins = data.iloc[:, 0]
        records = []
        for column in data.columns[1:]:
            counts = data[column]
            for x, c in enumerate(counts):
                if c != 0:
                    break
            min_v = bins[x]
            for x, c in enumerate(counts[::-1]):
                if c != 0:
                    break
            x += 1
            max_v = bins[-x]
            sums = bins * counts
            mean_v = float(sum(sums)) / sum(counts)

            cumul = counts.cumsum()
            nvalues = cumul.iloc[-1]
            median_value = nvalues // 2
            idx = cumul.searchsorted(median_value)[0]
            if cumul.iloc[idx] == median_value:
                median_v = (bins.iloc[idx] + bins.iloc[idx + 1]) / 2.0
            else:
                median_v = bins.iloc[idx]

            squared_diffs = (bins - mean_v) * (bins - mean_v) * counts
            std_v = math.sqrt(sum(squared_diffs) / nvalues)
            records.append(
                (nvalues, mean_v, std_v, min_v, median_v, max_v))

        return pandas.DataFrame.from_records(
            records,
            index=data.columns[1:],
            columns=["count", "mean", "std", "min", "50%", "max"])


class TransformerPairwise(Transformer):

    '''for each pair of columns on the lowest level compute
    the pearson correlation coefficient and other stats.
    '''

    nlevels = 0
    method = None
    paired = False

    # This transformer increases the number of levels
    # so do not prune.
    prune_dataframe = False

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

    def transform(self, data):
        self.debug("%s: called" % str(self))

        if len(data.columns) < 2:
            raise ValueError("expected at least two columns, "
                             "got only %s." %
                             str(data.columns))

        results = []
        pairs = []

        for x, y in itertools.combinations(data.columns, 2):

            xvals, yvals = data[x], data[y]
            if self.paired and False:
                if len(xvals) != len(yvals):
                    raise ValueError("expected two arrays of the "
                                     "same length, %i != %i" %
                                     (len(xvals),
                                      len(yvals)))

                take = [i for i in range(len(xvals))
                        if xvals[i] is not None and yvals[i] is not None
                        and type(xvals[i]) in (float, int)
                        and type(yvals[i]) in (float, int)]
                xvals = [xvals[i] for i in take]
                yvals = [yvals[i] for i in take]

            try:
                result = self.apply(numpy.array(xvals),
                                    numpy.array(yvals))
            except ValueError as msg:
                warn("pairwise computation failed: %s" % msg)
                continue
            results.append(result)
            pairs.append((x, y))

        if results:
            df = pandas.DataFrame(results,
                                  index=pandas.MultiIndex.from_tuples(pairs))
        else:
            return None

        return df


class TransformerCorrelation(TransformerPairwise):

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

    def apply(self, xvals, yvals):
        return Stats.doCorrelationTest(xvals, yvals,
                                       method=self.method)


class TransformerCorrelationPearson(TransformerCorrelation):

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


class TransformerCorrelationSpearman(TransformerCorrelation):

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


class TransformerMannWhitneyU(TransformerPairwise):

    '''apply the Mann-Whitney U test to test for
    the difference of medians.

    Example::

       Input:
       set1=[1,2,3,4,5,6,7,8,9,10]
       set2=[3,4,5,6,7,8,9,10,11,12]
       set3=[5,6,7,8,9,10,11,12,14,15]

       Output:


    '''

    def apply(self, xvals, yvals):
        xx = xvals[~numpy.isnan(xvals)]
        yy = yvals[~numpy.isnan(yvals)]
        r = Stats.doMannWhitneyUTest(xx, yy)
        return r


class TransformerContingency(TransformerPairwise):

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

    def apply(self, xvals, yvals):
        return len(set(xvals).intersection(set(yvals)))


class TransformerAggregate(Transformer):
    '''aggregate histogram like data.

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

    smooth
        smooth histogram.

    rarify
        take only a subset of columns from a histogram.
        Use with smoothing to visualize dense noisy histograms.
    '''

    nlevels = 0

    options = Transformer.options +\
        (('tf-aggregate', directives.unchanged),
         ('tf-smooth-window-size', directives.length_or_unitless),
         ('tf-rarify', directives.unchanged))

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.column_converters = []
        self.histogram_converters = []
        self.mFormat = "%i"
        self.mBinMarker = "left"

        self.mMapKeyword = {
            "normalized-max": self.normalize_max,
            "normalized-total": self.normalize_total,
            "cumulative": self.cumulate,
            "reverse-cumulative": self.reverse_cumulate,
            "relevel-with-first": self.relevel_with_first,
            "smooth": self.smooth_histogram,
        }

        self.map_histogram_converters = {
            "rarify": self.rarify,
            "fill_range_with_zeros": self.fill_range_with_zeros,
        }

        if "tf-aggregate" in kwargs:
            for x in kwargs["tf-aggregate"].split(","):
                if x in self.mMapKeyword:
                    self.column_converters.append(self.mMapKeyword[x])
                elif x in self.map_histogram_converters:
                    self.histogram_converters.append(self.map_histogram_converters[x])
                else:
                    raise KeyError("unknown keyword `%s`" % x)

        if self.normalize_total in self.column_converters or \
           self.normalize_max in self.column_converters:
            self.mFormat = "%6.4f"

        self.mBins = kwargs.get("tf-bins", "100")
        self.mRange = kwargs.get("tf-range", None)
        self.smooth_window_size = int(kwargs.get("tf-smooth-window-size", 11))
        self.rarify_ratio = float(kwargs.get("tf-rarify", 0.01))

        f = []
        if self.normalize_total in self.column_converters:
            f.append("relative")
        else:
            f.append("absolute")
        if self.cumulate in self.column_converters:
            f.append("cumulative")
        if self.reverse_cumulate in self.column_converters:
            f.append("cumulative")
        f.append("frequency")

        self.mYLabel = " ".join(f)

    def normalize_max(self, data):
        """normalize a data vector by maximum.
        """
        if data is None or len(data) == 0:
            return data
        m = max(data)
        data = data.astype(numpy.float)
        # numpy does not throw at division by zero, but sets values to Inf
        return data / m

    def smooth_histogram(self, data):
        r = Stats.smooth(data, window_len=self.smooth_window_size)
        return r[:len(data)]

    def relevel_with_first(self, data):
        """re-level data - add value of first bin to all other bins
        and set first bin to 0.
        """
        if data is None or len(data) == 0:
            return data
        v = data[0]
        data += v
        data[0] -= v
        return data

    def normalize_total(self, data):
        """normalize a data vector by the total"""
        if data is None or len(data) == 0:
            return data
        try:
            m = sum(data)
        except TypeError:
            return data
        data = data.astype(numpy.float)
        # numpy does not throw at division by zero, but sets values to Inf
        return data / m

    def cumulate(self, data):
        return data.cumsum()

    def reverse_cumulate(self, data):
        return data[::-1].cumsum()[::-1]

    def rarify(self, data):
        if self.rarify_ratio < 1:
            window = min(1, int(math.floor(len(data) * self.rarify_ratio)))
        else:
            window = min(1, int(math.floor(float(len(data)) / self.rarify_ratio)))
        return data.ix[range(0, len(data), window)]

    def fill_range_with_zeros(self, data):
        min_range = data.ix[:, 0].min()
        max_range = data.ix[:, 0].max()
        df = pandas.DataFrame(0,
                              index=numpy.arange(min_range, max_range),
                              columns=data.columns[1:]).reset_index()
        df.columns = data.columns
        merged = pandas.merge(df, data, on=data.columns[0], how="left").fillna(0)
        merged[data.columns[1]] = merged[data.columns[1] + "_x"] + merged[data.columns[1]+"_y"]
        merged = merged[data.columns]
        keys = tuple(data.groupby(by=data.index).groups.keys()[0])
        merged.index = pandas.MultiIndex.from_tuples(
            [keys] * len(merged),
            names=data.index.names)
        return merged

    def transform(self, data):
        self.debug("%s: called" % str(self))

        if len(data.columns) < 2:
            raise ValueError(
                'expected at least two columns, only got %s' %
                str(data.columns))

        for column in data.columns[1:]:
            for converter in self.column_converters:
                data.loc[:, column] = converter(data[column])

        for converter in self.histogram_converters:
            data = converter(data)

        return data


class TransformerHistogram(TransformerAggregate):
    '''compute a histogram of columns in the data
    frame.

    Returns a new dataframe with an additional
    first column called 'bins'.

    The bin-marker is placed on the left of the bin.
    '''

    nlevels = 0

    options = Transformer.options +\
        (('tf-bins', directives.unchanged),
         ('tf-range', directives.unchanged),
         ('tf-max-bins', directives.unchanged),
         )

    def __init__(self, *args, **kwargs):
        TransformerAggregate.__init__(self, *args, **kwargs)

        self.mFormat = "%i"
        self.mBinMarker = "left"

        self.mBins = kwargs.get("tf-bins", "100")
        self.mRange = kwargs.get("tf-range", None)
        self.max_bins = int(kwargs.get("max-bins", "1000"))

        f = []
        if self.normalize_total in self.column_converters:
            f.append("relative")
        else:
            f.append("absolute")
        if self.cumulate in self.column_converters:
            f.append("cumulative")
        if self.reverse_cumulate in self.column_converters:
            f.append("cumulative")
        f.append("frequency")

        self.mYLabel = " ".join(f)

    def binToX(self, bins):
        """convert bins to x-values."""
        if self.mBinMarker == "left":
            return bins[:-1]
        elif self.mBinMarker == "mean":
            return [(bins[x] - bins[x - 1]) / 2.0 for x in range(1, len(bins))]
        elif self.mBbinMarker == "right":
            return bins[1:]

    def toHistogram(self, data):
        '''compute the histogram.'''

        if len(data) == 0:
            self.warn("empty histogram")
            return None

        binsize = None

        if self.mRange is not None:
            vals = [x.strip() for x in self.mRange.split(",")]
            if len(vals) == 3:
                mi, ma, binsize = vals[0], vals[1], float(vals[2])
            elif len(vals) == 2:
                mi, ma, binsize = vals[0], vals[1], None
            elif len(vals) == 1:
                mi, ma, binsize = vals[0], None, None
            if mi is None or mi == "":
                mi = min(data.min())
            else:
                mi = float(mi)
            if ma is None or ma == "":
                ma = max(data.max())
            else:
                ma = float(ma)
        else:
            mi, ma = min(data.min()), max(data.max())

        if self.mBins.startswith("dict"):
            h = collections.defaultdict(int)
            for x in data:
                h[x] += 1
            bin_edges = sorted(h.keys())
            hist = numpy.zeros(len(bin_edges), numpy.int)
            for x in range(len(bin_edges)):
                hist[x] = h[bin_edges[x]]
            bin_edges.append(bin_edges[-1] + 1)
        else:
            if self.mBins.startswith("log"):

                try:
                    a, b = self.mBins.split("-")
                except ValueError:
                    raise SyntaxError("expected log-xxx, got %s" % self.mBins)
                nbins = float(b)
                if ma < 0 or mi < 0:
                    raise ValueError(
                        "can not bin logarithmically for negative values.")
                if mi == 0:
                    mi = numpy.MachAr().epsneg
                ma = numpy.log10(ma)
                mi = numpy.log10(mi)
                try:
                    bins = [10 ** x for x in numpy.arange(mi, ma, ma / nbins)]
                except ValueError as msg:
                    raise ValueError("can not compute %i bins for %f-%f: %s" %
                                     (nbins, mi, ma, msg))
            elif binsize is not None:
                # AH: why this sort statement? Removed
                # data.sort()

                # make sure that ma is part of bins
                bins = numpy.arange(mi, ma + binsize, binsize)
            else:
                try:
                    bins = eval(self.mBins)
                except SyntaxError as msg:
                    raise SyntaxError(
                        "could not evaluate bins from `%s`, error=`%s`"
                        % (self.mBins, msg))

            if hasattr(bins, "__iter__"):
                if len(bins) == 0:
                    warn("empty bins")
                    return None, None
                if self.max_bins > 0 and len(bins) > self.max_bins:
                    # truncate number of bins
                    warn("too many bins (%i) - truncated to (%i)" %
                         (len(bins), self.max_bins))
                    bins = self.max_bins

            # ignore histogram semantics warning
            all_counts = []
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for column in data.columns:
                    counts, bin_edges = numpy.histogram(
                        data[column],
                        bins=bins, range=(mi, ma))
                    all_counts.append(counts)
            bin_edges = self.binToX(bin_edges)

            # re-build dataframe
            df = pandas.DataFrame.from_items(
                [('bin', bin_edges)] + zip(
                    data.columns, all_counts))

        return df

    def transform(self, data):
        self.debug("%s: called" % (str(self)))

        df = self.toHistogram(data)
        df = df.set_index("bin", append=True)
        for converter in self.column_converters:
            df = df.apply(converter, axis=0)

        df.reset_index(level="bin", inplace=True)
        self.debug("%s: completed" % (str(self)))
        return df


class TransformerMelt(Transformer):
    '''Create a melted table

    '''

    nlevels = None

    def __call__(self, data):
        ''' returns a melted table'''
        # merge index into dataframe
        # melt

        return pandas.melt(data.reset_index(), data.index.names)


class TransformerPivot(Transformer):
    '''pivot a table using pandas.pivot_table.

    Requires to define three columns in the
    dataframe to determine the row labels,
    column labels and values in the new dataframe.
    '''

    nlevels = None

    options = Transformer.options +\
        (('pivot-index', directives.unchanged),
         ('pivot-column', directives.unchanged),
         ('pivot-value', directives.unchanged),
         ('missing-value', directives.unchanged),
         )

    pivot_index = None
    pivot_column = None
    pivot_value = None
    missing_value = None

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        def _get_value(name):

            c = "pivot-{}".format(name)
            if c not in kwargs:
                raise ValueError('pivot requires a column to use as {} (--{})'
                                 .format(name, c))
            # convert to string, otherwise it is
            # docutils.nodes.reprunicode which does not evaluate as a
            # scalar in numpy and causes df.pivot() to fail.
            v = str(kwargs[c])
            if "," in v:
                v = [x.strip() for x in v.split(",")]
            return v

        self.pivot_index = _get_value("index")
        self.pivot_column = _get_value("column")
        self.pivot_value = _get_value("value")
        self.missing_value = kwargs.get("missing-value", None)

    def __call__(self, data):

        df = pandas.pivot_table(
            data.reset_index(),
            index=self.pivot_index,
            columns=self.pivot_column,
            values=self.pivot_value)

        if self.missing_value is not None:
            try:
                v = float(self.missing_value)
            except ValueError:
                v = self.missing_value
            df.fillna(v, inplace=True)

        return df
