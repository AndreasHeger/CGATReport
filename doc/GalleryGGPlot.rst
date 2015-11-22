.. _ggplot:

======
ggplot
======

The :class:`CGATReportPlugins.GGPlotter.GGPlot` displays
a dataframe using the python port (ggplot_) of the ggplot2_ package.

.. note::

   As of pandas 0.16.0, the following error will appear here for older
   versions of ggplot:

   ``pivot_table() got an unexpected keyword argument ‘rows’``

   Please see: https://github.com/yhat/ggplot/issues/417.
   Make sure you have the latest version (>= 0.6.8) installed.
   
.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: 'value', color='track'
   :geom: geom_histogram()
   :layout: column-2
   :width: 300

   A histogram plot. Each track is plotted in a separate plot.

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: 'value', color='track'
   :geom: geom_histogram()
   :layout: column-2
   :groupby: all
   :width: 300

   A histogram plot, all data grouped so that they are plotted
   in the same plot.

Options
-------

:class:`CGATReportPlugins.GGPlotter.GGPlot` understands the
following options:

.. glossary::
   :sorted:

   aes
      aesthaetics to use. This is the expression within the
      aes( ) statement.

   geom
      geometry to use and any other modifications to the plot.

Both :term:`aes` :term:`geom` are evaluated in a namespace where
all names from ggplot_, numpy_ and pandas_ have been imported. Note
that column names in the dataframe need to be enclosed by quotation
marks as they are interpreted as strings.

For more information about plotting with the ggplot_ library, see
its documentation.

