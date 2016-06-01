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

To follow the examples from `here <http://pandas.pydata.org/pandas-docs/stable/visualization.html>`_:

.. report:: Trackers.TableTimeSeries
   :render: pdplot

   Simple time series

.. report:: Trackers.TableTimeSeries
   :render: pdplot
   :statement: kind="kde"

   Density plot

.. report:: Trackers.TableTimeSeries
   :render: pdplot
   :statement: subplots=True

   Plotting with subplots

.. report:: Trackers.TableTimeSeries
   :render: pdplot
   :statement: kind="area", stacked=False

   Area plots
