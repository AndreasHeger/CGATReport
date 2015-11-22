.. _pdplot:

======
pdplot
======

The :class:`CGATReportPlugins.PandasPlotter.PandasPlot` displays
a dataframe using the pandas plot() method.

.. report:: Trackers.MultipleColumnDataExample
   :render: pdplot
   :statement: kind="scatter", x="col1", y="col2"
   :layout: column-2
   :width: 300

   A scatter plot
