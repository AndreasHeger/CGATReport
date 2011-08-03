============
scatter-plot
============

The :class:`SphinxReportPlugins.Plotter.ScatterPlot` class presents
:term:`numerical arrays` as a scatter plot.

.. report:: Trackers.MultipleColumnDataExample
   :render: scatter-plot
   :layout: row
   :width: 200

   A scatter plot.

Options
=======

:class:`SphinxReportPlugins.Plotter.ScatterPlot` has no additional
options apart from :ref:`common plot options`. 


====================
rainbow-scatter-plot
====================

The :class:`SphinxReportPlugins.Plotter.ScatterPlotWithColour` class presents
:term:`data arrays` as a scatter plot.


A scatter plot with colours

.. report:: Trackers.MultipleColumnDataFullExample
   :render: scatter-rainbow-plot

   A scatter plot with colours.

A scatter plot built from single trackers using the :class:`Transformer.TransformerCombinations`
transformer. 

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


Options
=======

:class:`SphinxReportPlugins.Plotter.ScatterPlotWithColour` has no additional
options apart from :ref:`common plot options`. 
