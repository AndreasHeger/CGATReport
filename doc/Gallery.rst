*******
Gallery
*******

The gallery lists examples of all plots and available renderers.

Labeled data
************

These Renderers require :class:`DataTypes.LabeledData`. Labeled data is
consists of a list of labels and a list of data, for
example ``[ ("column1", "column2" ), ( 10, 20) ]``.

Table
=====

The :class:`Renderer.RendererTable` class inserts labeled data into
a table.

.. report:: Trackers.LabeledDataExample
   :render: table

   A table.

Stacked Barplot
===============

The :class:`Renderer.RendererStackedBars` class presents labeled data
as stacked bars.

.. report:: Trackers.LabeledDataExample
   :render: stacked-bars

   A bar plot with stacked bars.

Interleaved Barplot
===================

The :class:`Renderer.RendererInterleavedBars` class presents labeled data
as interleaved bars. Both *interleaved-bars* and *bars* can be used.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bars

   A bar plot with interleaved bars.

Pie plot
========

The :class:`Renderer.RendererPiePlot` class presents labeled data
as pie charts.

.. report:: Trackers.LabeledDataExample
   :render: pie-plot

   A pie plot

Single column data
******************

Renderers that accept a single column of data of type :class:`DataTypes.SingleColumnData` 
per :term:`track` and :term:`slice`, for example ``[2,3,1,3,4]``.

Histogram
=========

The :class:`Renderer.RendererHistogram` class computes a histogram
of data and inserts it as a table.

.. report:: Trackers.SingleColumnDataExample
   :render: table
   :transform: histogram
   :bins: arange(0,10)

   A histogram.

HistogramPlot
=============

The :class:`Renderer.RendererLinePlot` class computes a histogram
of data and inserts a plot.

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :bins: arange(0,10)

   A histogram plot.

Stats
=====

The :class:`Transformer.TransformerStats` class computes summary
statistics and displays them in a table.

.. report:: Trackers.SingleColumnDataExample
   :render: table
   :transform: stats

   A table.

Boxplot
=======

The :class:`Renderer.RendererBoxplot` class computes boxplots.

.. report:: Trackers.SingleColumnDataExample
   :render: box-plot

   Figure caption.

Multi-column data
*****************

Renderers that accept multiple columns of data of type :class:`DataTypes.SingleColumnData` 
per :term:`track` and :term:`slice`. The data is asscociated with column headers, for example 
``[ ('column1', 'column2'), ( ( 1,2,3), (4,5,6) )]``.

Pairwise statistics table
=========================

Compute correlation statistics between all columns.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: correlation

   A pairwise statistics table.

.. Pairwise statistics plot
.. ========================

.. Plot correlation coefficients between all columns.

.. .. report:: Trackers.MultipleColumnDataExample
..    :render: table
..    :transform: filter

..    A pairwise statistics plot.

Pairwise scatter plot
========================

A scatter plot.

.. report:: Trackers.MultipleColumnDataExample
   :render: scatter-plot

   A scatter plot.

A scatter plot with colours

.. report:: Trackers.MultipleColumnDataExample
   :render: scatter-rainbow-plot

   A scatter plot with colours.


Grouped table
=============

A grouped table.

.. report:: Trackers.MultipleColumnsExample
   :render: table

   A grouped table.

Matrices
========

The :class:`Renderer.RendererMatrix` class inserts labeled data into
a matrix:

.. report:: Trackers.LabeledDataExample
   :render: matrix

   A matrix.

The :class:`Renderer.RendererMatrixPlot` class inserts labeled data into
a table.

.. report:: Trackers.LabeledDataExample
   :render: matrix-plot

   A matrix.

The :class:`Renderer.RendererHintonPlot` class inserts labeled data into
a table.

.. report:: Trackers.LabeledDataExample
   :render: hinton-plot

   A matrix.
