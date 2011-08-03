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
      cumulative|reverse-cumulative|normalized-max|normalized-total

      normalize or cumulate values in a histogram

      * normalized-max - normalize histogram with maximum value
      * normalized-total - normalize histogram with sum of values
      * cumulative - compute cumulative histogram
      * reverse-cumulative - compute reverse cumulative histogram
      
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


