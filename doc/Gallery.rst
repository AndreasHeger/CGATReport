*******
Gallery
*******

The gallery lists examples of all plots and available renderers.

Table
=====

The :class:`Renderer.RendererTable` class inserts labeled data into
a table.

.. report:: Trackers.LabeledDataExample
   :render: table

   A table.

Barplot
=======

The :class:`Renderer.RendererBarPlot` class presents labeled data
as overlapping bars.

.. report:: Trackers.LabeledDataExample
   :render: bar-plot

   A bar plot with overlapping bars.

Stacked Barplot
===============

The :class:`Renderer.RendererStackedBarPlot` class presents labeled data
as stacked bars.

.. report:: Trackers.LabeledDataExample
   :render: stacked-bar-plot

   A bar plot with stacked bars.

Interleaved Barplot
===================

The :class:`Renderer.RendererInterleavedBarPlot` class presents labeled data
as interleaved bars. Both *interleaved-bars* and *bars* can be used.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot

   A bar plot with interleaved bars.

Pie plot
========

The :class:`Renderer.RendererPiePlot` class presents labeled data
as pie charts.

.. report:: Trackers.LabeledDataExample
   :render: pie-plot

   A pie plot

Histogram
=========

The :class:`Renderer.RendererHistogram` class computes a histogram
of data and inserts it as a table.

.. report:: Trackers.SingleColumnDataExample
   :render: table
   :transform: histogram
   :tf-bins: arange(0,10)

   A histogram.

HistogramPlot
=============

A histogram is plotted as a combination of a 
:class:`Renderer.RendererLinePlot` 
and a :class:`Transformer.TransformerHistogram`.

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)

   A histogram plot.

Histogram as gradient
=====================

A histogram is plotted as a combination of a 
:class:`Renderer.RendererLinePlot` 
and a :class:`Transformer.TransformerHistogram`.

.. report:: Trackers.SingleColumnDataExample
   :render: histogram-gradient-plot
   :transform: histogram
   :tf-bins: arange(0,10)

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

Pairwise scatter plot
========================

A scatter plot plotting multiple values

.. report:: Trackers.MultipleColumnDataExample
   :render: scatter-plot

   A scatter plot.

A scatter plot with colours

.. report:: Trackers.MultipleColumnDataFullExample
   :render: scatter-rainbow-plot

   A scatter plot with colours.

A scatter plot with pairwise variables, multiple plots:

.. report:: Trackers.SingleColumnDataExample
   :render: scatter-plot
   :transform: combine
   :tf-fields: data
   :groupby: track

   A scatter plot from single columns

A scatter plot with pairwise variables, single plot:

.. report:: Trackers.SingleColumnDataExample
   :render: scatter-plot
   :transform: combine
   :tf-fields: data

   A scatter plot from single columns

Grouped table
=============

A grouped table.

.. report:: Trackers.MultipleColumnsExample
   :render: table

   A grouped table.

Matrices
========

The :class:`Renderer.RendererMatrix` class display labeled data into
a tabular matrix:

.. report:: Trackers.LabeledDataExample
   :render: matrix

   A matrix.

The :class:`Renderer.RendererMatrixPlot` class plots labeled data
in a matrix plot.

.. report:: Trackers.LabeledDataExample
   :render: matrix-plot

   A matrix.

The :class:`Renderer.RendererHintonPlot` plots labeled data as a
weight matrix. The width and colour of each box shows the weight. 

.. report:: Trackers.LabeledDataExample
   :render: hinton-plot

   A matrix.

The :class:`Renderer.RendererHintonPlot` plots labeled data as a
weight matrix. The width of each box shows the weight. Additional
labels can provide colours.

.. report:: Trackers.LabeledDataWithErrorsExample
   :render: hinton-plot
   :colour: error

   A matrix.

Transformers
************

Correlation
===========

Compute correlation statistics between all columns within a tracker.

.. report:: Trackers.MultipleColumnDataExample
   :render: table
   :transform: correlation

   A pairwise statistics table.

Correlation
===========

Compute correlation statistics between tracks/slices for a single column

.. report:: Trackers.SingleColumnDataExample
   :render: table
   :transform: select,correlation
   :tf-fields: data

   A pairwise statistics table.

Correlation
===========

Compute correlation statistics between tracks/slices for a single column

.. report:: Trackers.SingleColumnDataExampleWithoutSlices
   :render: table
   :transform: select,correlation
   :tf-fields: data

   A pairwise statistics table.

Filter
======

Compute correlation statistics between all columns.

.. report:: Trackers.MultipleColumnDataExample
   :render: matrix
   :transform: correlation,select
   :tf-fields: coefficient
   :format: %6.4f

   Matrix of correlation coefficients

