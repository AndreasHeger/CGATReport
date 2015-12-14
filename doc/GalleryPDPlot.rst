.. _pdplot:

======
pdplot
======

The :class:`CGATReportPlugins.PandasPlotter.PandasPlot` displays a
dataframe using the pandas_ `plot
<http://pandas.pydata.org/pandas-docs/stable/visualization.html>`_
method.

.. report:: Trackers.MultipleColumnDataExample
   :render: pdplot
   :statement: kind="scatter", x="col1", y="col2"
   :layout: column-2
   :width: 300

   A scatter plot
