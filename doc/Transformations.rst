.. _transformers:

============
Transformers
============

Transformers change data before rendering. They are called by the
``:transform:`` option. Transformers can be combined in a
comma-separated list.

.. _pandas:

pandas
======

The :class:`CGATReportPlugins.Transformer.Pandas` applies pandas
dataframe methods to the current data frame::

  .. report:: Trackers.MultipleColumnDataExample
     :render: debug
     :transform: pandas
     :tf-statement: reset_index().set_index('slice','track')

     use pandas methods to reorder the index.

.. report:: Trackers.MultipleColumnDataExample
   :render: debug
   :transform: pandas
   :tf-statement: reset_index().set_index('slice','track')

   use pandas methods to reorder the index.

.. _stats:

stats
=====

The :class:`CGATReportPlugins.Transformer.Stats` class computes
summary statistics of a :term:`numerical array`::

  .. report:: Trackers.SingleColumnDataExample
     :render: table
     :transform: stats

     A table.

.. report:: Trackers.SingleColumnDataExample
   :render: table
   :transform: stats

   A table.

.. _correlation:

.. _stats:

histogram-stats
===============

The :class:`CGATReportPlugins.Transformer.HistogramStats` class computes
summary statistics from :term:`numerical arrays`, where the first
array is assumed to be bins and remaining columns are counts. Values
are only exact for integer valued bins and where all values correspond
to bins::

  .. report:: Transformers.TrackerHistogramStats
     :render: table
     :transform: histogram-stats

     A table.

.. report:: Transformers.TrackerHistogramStats
   :render: table
   :transform: histogram-stats

   A table.

.. _correlation:

correlation
===========

synonymous to :ref:`pearson`.

.. _pearson:

pearson
=======

The
:class:`CGATReportPlugins.Transformer.TransformerCorrelationPearson`
class computes Pearson correlation statistics between two or more
:term:`numerical arrays`.  Each possible combination of arrays is
tested and for each comparison a new dictionary is inserted with the
result of the test::

  .. report:: Trackers.MultipleColumnDataExample
     :render: table
     :transform: pearson

     A pairwise statistics table.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: pearson

   A pairwise statistics table.

.. _spearman:

spearman
========

The :class:`CGATReportPlugins.Transformer.TransformerCorrelationPearson` class computes
Spearman correlation statistics between two or more :term:`numerical
arrays`. Each possible combination of arrays is tested and for each
comparison a new dictionary is inserted with the result of the test::

  .. report:: Trackers.MultipleColumnDataExample
     :render: table
     :transform: spearman

     A pairwise statistics table.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: spearman

   A pairwise statistics table.

.. _test-mwu:

test-mwu
========

The :class:`CGATReportPlugins.Transformer.TransformerMannWhitneyU`
class computes Mann-Whitney U test to test for the difference of medians
between two or more :term:`numerical
arrays`. Each possible combination of arrays is tested and for each
comparison a new dictionary is inserted with the result of the test::

  .. report:: Trackers.MultipleColumnDataExample
     :render: table
     :transform: test-mwu

     A pairwise statistics table.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: test-mwu

   A pairwise statistics table.

.. _select:

..
   select
   ======

   The :class:`CGATReportPlugins.Transformer.TransformerSelect` selects
   one field from a :term:`data tree`.

     .. report:: Trackers.SingleColumnDataExample
	:render: table
	:transform: select,correlation
	:tf-fields: data

	A pairwise statistics table.

   .. report:: Trackers.SingleColumnDataExample
      :render: table
      :transform: select,correlation
      :tf-fields: data

      A pairwise statistics table.

   Options
   -------

   The :class:`CGATReportPlugins.Transformer.TransformerSelect` understands the
   following options:

   .. glossary::

      tf-fields
	 string

	 fields to select. This option is required.

   Without slices
   --------------

   Compute correlation statistics between tracks/slices for a single column

   .. report:: Trackers.SingleColumnDataExampleWithoutSlices
      :render: table
      :transform: select,correlation
      :tf-fields: data

      A pairwise statistics table.

   Compute correlation statistics between all columns.

   .. report:: Trackers.MultipleColumnDataExample
      :render: matrix
      :transform: correlation,select
      :tf-fields: coefficient
      :format: %6.4f

      Matrix of correlation coefficients

.. _filter:

filter
======

The :class:`CGATReportPlugins.Transformer.TransformerFilter` removes
one or more fields from a :term:`data tree`:

Input:

.. report:: Trackers.MultipleColumnDataExample
   :render: dataframe
   :head: 5
    
   Input data

Transformation::

   .. report:: Trackers.MultipleColumnDataExample
      :render: dataframe
      :transform: filter
      :tf-fields: col1

      Output

Output:

.. report:: Trackers.MultipleColumnDataExample
   :render: dataframe
   :head: 5
   :transform: filter
   :tf-fields: col1

   Output

Options
-------

The :class:`CGATReportPlugins.Transformer.TransformerFilter` understands the
following options:

.. glossary::

   tf-fields
      string

      fields to select. This option is required.

   tf-level
      int

      level in the :term:`data tree` on which to act.

.. _histogram:

histogram
=========

The :class:`CGATReportPlugins.Transformer.Histogram` class computes a histogram
of ``numerical array` and inserts it as a table.

Input:

.. report:: Trackers.SingleColumnDataExample
   :render: dataframe
   :head: 5
   :tail: 5

   Input data

Transformation::

   .. report:: Trackers.SingleColumnDataExample
      :render: dataframe
      :transform: histogram
      :tf-bins: arange(0,10)

      A histogram.

Output:

.. report:: Trackers.SingleColumnDataExample
   :render: dataframe
   :transform: histogram
   :tf-bins: arange(0,10)
   :head: 5
   :tail: 5
  
   A histogram.

Options
-------

The :class:`CGATReportPlugins.Transformer.Histogram` understands the
following options:

.. glossary::
   :sorted:
   
   tf-aggregate
      cumulative|reverse-cumulative|normalized-max|normalized-total|relevel-first

      normalize or cumulate values in a histogram

      * normalized-max - normalize histogram with maximum value
      * normalized-total - normalize histogram with sum of values
      * cumulative - compute cumulative histogram
      * reverse-cumulative - compute reverse cumulative histogram
      * relevel-first - relevel by adding the first bin to all others.
        
      
   tf-bins
      int or sequence of scalars, optional

      If `tf-bins` is an int, it defines the number of equal-width
      bins in the given range (10, by default). If `bins` is a sequence,
      it defines the bin edges, including the rightmost edge, allowing
      for non-uniform bin widths.
      (From the cgatreport`numpy` documentation)
      If bins is of the format ''log-X'' with X an integer number, X 
      logarithmig bins will be used. 
      If bins is ''dict'', then the histogram will be computed using a
      dictionary. Use this for large data sets, but make sure to round
      values reasonably.

      Examples::

	 :tf-bins: 100
	 :tf-bins: arange(0,1,0.1)
	 :tf-bins: log-100

   tf-range
      float[,float[,float]], optional

      The minimum value, maximum value and the bin-size. Fields can the left empty.
      If no minimum is provided, the minimum value is min(data), the maxmimum
      value is max(data) and the bin-size depends on the :term:`tf-bins` parameter.
      Values outside the range are ignored. 

Working with multiple columns
-----------------------------

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :layout: row
   :width: 200

   A histogram plot.


.. _aggregate:

aggregate
=========

The :class:`CGATReportPlugins.Transformer.Aggregate` takes
histogrammed data and performs various aggregation or normalization
tasks. The dataframe needs to have two columns and the aggregation
is performed on all columns but the first, which is assumed
to be the histogram bins.

Input:

.. report:: Trackers.ArrayDataExample
   :render: dataframe
   :head: 5
   :tail: 5
      		  
   Input data

Transformation::

   .. report:: Trackers.ArrayDataExample
      :render: line-plot
      :transform: aggregate
      :tf-aggregate: cumulative

      Data output

Output:

.. report:: Trackers.ArrayDataExample
   :render: dataframe
   :transform: aggregate
   :tf-aggregate: cumulative
   :head: 5
   :tail: 5
      		  
   Cumulative data.

..
   .. _tolist:

   toList
   ======

   The :class:`CGATReportPlugins.Transformer.List` takes
   labeled data and converts it into lists. For example,
   if you have the following data::

      data1/x/1/2   data1/y/1/4
      data2/x/2/4   data2/y/2/5
      data3/x/3/3   data3/y/3/5
      data4/x/4/4   data4/y/4/6

   Transformation results in:

      x/(2,4,3,4)
      y/(4,5,5,6)

   Note how the higher level of the path is discarded. The operation is
   in some ways the reverse of the :ref:`tolables` transformation.

..
   .. _group:

   group
   =====

   .. _indicator:

   indicator
   =========

   .. _tolabels:

   tolabels
   ========

   The :class:`CGATReportPlugins.Transformer.TransformerToLabels` converts
   :term:`numerical arrays` to :term:`labeled data`. Imagine you have the following
   data::

      data1/x/(2,4,3,4)
      data1/y/(4,5,5,6)

   These data can be displayed as a :ref:`scatter-plot` or a :ref:`line-plot`. However,
   if you tried displaying these as a :ref:`bar-plot` you will get a ``malformatted data``
   error message as :ref:`bar-plot` expects :term:`labeled data`. 

   The :ref:`tolabels` transformation can help transform the data. In the example above,
   the transformation would result in::

      data1/x/1/2   data1/y/1/4
	   /x/2/4        /y/2/5
	   /x/3/3        /y/3/5
	   /x/4/4        /y/5/6

      .. report:: Trackers.MultipleColumnDataExample
	 :render: interleaved-bar-plot
	 :transform: tolabels

	 An interleaved bar plot

   .. report:: Trackers.MultipleColumnDataExample
      :render: interleaved-bar-plot
      :transform: tolabels

       An interleaved bar plot

   Options
   -------

   The :class:`CGATReportPlugins.Transformer.TransformerFilter` understands the
   following options:

   .. glossary::

      tf-fields
	 string

	 fields to select. This option is required.

      tf-level
	 int

	 level in the :term:`data tree` on which to act.

.. _melt:

melt
====

The :class:`CGATReportPlugins.Transformer.TransformerMelt` creates a
melted table. See
`here <http://scienceoss.com/restructure-or-reformat-dataframes-in-r-with-melt>`_
for an example.

CGATReport will call the
`melt <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.melt.html>`_
function in pandas_, the index will be used as the ``identifier``
variables and all columns as ``value`` variables.  For example, melting the
following dataframe:

.. report:: Trackers.MultipleColumnDataExample
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Input dataframe

Transformation::

    .. report:: Trackers.MultipleColumnDataExample
       :render: dataframe
       :groupby: all
       :transform: melt

       Output

will result in:

.. report:: Trackers.MultipleColumnDataExample
   :render: dataframe
   :groupby: all
   :transform: melt
   :head: 5
   :tail: 5

   Output dataframe

:class:`CGATReportPlugins.Transformer.TransformerMelt` has no options.

.. _venn:

venn
====

The :class:`CGATReportPlugins.TransformersGeneLists.TransformerVenn`
takes a dictionary of lists and transforms the data so that it is in
the correct format for plotting a venn diagram of the overlaps between
the lists. This :term:`Transformer` understand the following options:

.. glossary::

   keep-background
      flag

      keep background data


.. _hypergeometric:

hypergeometric
==============

The :class:`CGATReportPlugins.TransformersGeneLists.TransformerHypergeometric`
takes a dictionary of lists and calculates the enrichements and
p-values for the overlaps using the hypergeometric distribution. If
there are more than two lists, all pairwise combinations will be
computed. This :term:`Transformer` has no options.

.. _p-adjust:

p-adjust
========

The :class:`CGATReportPlugins.TransformersGeneLists.TransformerMultiTest`
looks for a P-value column in a table and computes multiple testing
corrected p-values and adds these as a new column to the table.

By default all p-values from all levels are corrected together. In
order to change this behavoir use the adj-levels option.  The
original data tree is returned with an added P-adjust entry. The
default method for correction is BH, but other R style correction
methods can be specified with the option `adj-method`.

This :term:`Transformer` has the following options:

.. glossary::

   adj-level
      int

      Group tests from all levels below for adjustment.

   adj-method
      choice

      Method to use to compute adjusted P-Values. See the R
      documentation for p.adjust for available methods.

    p-value
      string

      String to identify the field in the table containing
      the p-values. The default is ``P-value``.


.. _count:

count
=====

The :class:`CGATReportPlugins.Transformer.TransformerCount` computes
the numbers of values in a data tree. Displaying a table of counts can often be useful to
summarize the number of entries in a list prior to plotting.

This :term:`Transformer` has the following options:

.. glossary::

   level
      int

      Level in the :term:`datatree` hierarchy at which to count.





