======
ggplot
======

The :class:`SphinxReportPlugins.GGPlotter.GGPlot` displays
a dataframe using the python port (ggplot_) of the ggplot2_ package.

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :transform: melt
   :aes: 'Data', color='Track'
   :geom: geom_histogram()
   :layout: column-2

   A histogram plot

Options
-------

:class:`SphinxReportPlugins.GGPlotter.GGPlot` understands the
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
