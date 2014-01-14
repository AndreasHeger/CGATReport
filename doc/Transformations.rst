.. _transformers:

============
Transformers
============

Transformers change data before rendering. They are called by the
``:transform:`` option. Transformers can be combined in a ``,``
separated list.

.. _stats:

stats
=====

The :class:`SphinxReportPlugins.Transformer.Stats` class computes
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

correlation
===========

synonymous to :ref:`pearson`.

.. _pearson:

pearson
=======

The :class:`SphinxReportPlugins.Transformer.TransformerCorrelationPearson` class computes
Pearson correlation statistics between two or more :term:`numerical
arrays`. 
Each possible combination of arrays is tested and for each
comparison a new dictionary is inserted with the result of the test.

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

The :class:`SphinxReportPlugins.Transformer.TransformerCorrelationPearson` class computes
Spearman correlation statistics between two or more :term:`numerical
arrays`. Each possible combination of arrays is tested and for each
comparison a new dictionary is inserted with the result of the test.

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

The :class:`SphinxReportPlugins.Transformer.TransformerMannWhitneyU`
class computes Mann-Whitney U test to test for the difference of medians
between two or more :term:`numerical
arrays`. Each possible combination of arrays is tested and for each
comparison a new dictionary is inserted with the result of the test.

  .. report:: Trackers.MultipleColumnDataExample
     :render: table
     :transform: test-mwu

     A pairwise statistics table.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: test-mwu

   A pairwise statistics table.

.. _select:

select
======

The :class:`SphinxReportPlugins.Transformer.TransformerSelect` selects
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

The :class:`SphinxReportPlugins.Transformer.TransformerSelect` understands the
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

The :class:`SphinxReportPlugins.Transformer.TransformerFilter` removes
one or more fields from a :term:`data tree`.

  .. report:: Trackers.MultipleColumnDataExample
     :render: line-plot
     :transform: histogram,filter
     :tf-bins: arange(0,10)
     :tf-fields: col1
     :tf-level: 2
     :layout: row
     :width: 200

     A histogram plot, but only with *col1* selected

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram,filter
   :tf-bins: arange(0,10)
   :tf-fields: col1
   :tf-level: 2
   :layout: row
   :width: 200

   A histogram plot, but only with *col1* selected

Options
-------

The :class:`SphinxReportPlugins.Transformer.TransformerFilter` understands the
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

The :class:`SphinxReportPlugins.Transformer.Histogram` class computes a histogram
of ``numerical array` and inserts it as a table::

   .. report:: Trackers.SingleColumnDataExample
      :render: line-plot
      :transform: histogram
      :tf-bins: arange(0,10)

      A histogram.

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :layout: row
   :width: 200
  
   A histogram.

Options
-------

The :class:`SphinxReportPlugins.Transformer.Histogram` understands the
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
      (From the sphinxreport`numpy` documentation)
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


.. Multihistogram plot
.. ===================

.. .. report:: TestCases.MultipleHistogramTest
..    :render: multihistogram-plot
..    :as-lines:
..    :layout: grid
..    :mpl-rc: figure.figsize=(3,3)

..    testing multiple histograms with grid layout.

.. _aggregate:

aggregate
=========

The :class:`SphinxReportPlugins.Transformer.Aggregate` takes
histogrammed data and performs various aggregation or normalization
tasks.

The transformer expects dictionaries of lists of numerical values. 
The first list is assumed to be bins and not transformed.

   .. report:: Trackers.ArrayDataExample
      :render: line-plot
      :transform: aggregate
      :tf-aggregate: cumulative
      		  
      cumulative data

.. report:: Trackers.ArrayDataExample
   :render: line-plot
   :transform: aggregate
   :tf-aggregate: cumulative
      		  
   cumulative data

.. _tolist:

toList
======

The :class:`SphinxReportPlugins.Transformer.List` takes
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

.. _group:

group
=====

.. _indicator:

indicator
=========

.. _tolabels:

tolabels
========

The :class:`SphinxReportPlugins.Transformer.TransformerToLabels` converts
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

The :class:`SphinxReportPlugins.Transformer.TransformerFilter` understands the
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

The :class:`SphinxReportPlugins.Transformer.TransformerMelt` creates a melted table. See
`<http://scienceoss.com/restructure-or-reformat-dataframes-in-r-with-melt>
here`_ for an example.

For example::

        Input:                                 Output
        experiment1/Sample1 = [1]              Track = ["experiment1","experiment1","experiment2","experiment2"]
        experiment1/Sample2 = [3]              Slice = ["Sample1","Sample2","Sample1","Sample2"]
        experiment2/Sample1 = [1]              Data =  [1,3,1,3]
        experiment2/Sample2 = [3]

:class:`SphinxReportPlugins.Transformer.TransformerMelt` has no options.

.. _venn:

venn
====

The :class:`SphinxReportPlugins.TransformersGeneLists.TransformerVenn`
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

The :class:`SphinxReportPlugins.TransformersGeneLists.TransformerHypergeometric`
takes a dictionary of lists and calculates the enrichements and
p-values for the overlaps using the hypergeometric distribution. If
there are more than two lists, all pairwise combinations will be
computed. This :term:`Transformer` has no options.

.. _p-adjust:

p-adjust
========

The :class:`SphinxReportPlugins.TransformersGeneLists.TransformerMultiTest`
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

The :class:`SphinxReportPlugins.Transformer.TransformerCount` computes
the numbers of values in a data tree. Displaying a table of counts can often be useful to
summarize the number of entries in a list prior to plotting.

This :term:`Transformer` has the following options:

.. glossary::

   level
      int
      
      Level in the :term:`datatree` hierarchy at which to count.





