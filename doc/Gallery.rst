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

