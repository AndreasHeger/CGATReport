.. _ggplot:

======
ggplot
======

The :class:`CGATReportPlugins.GGPlotter.GGPlot` displays a dataframe
using the plotnine_ package.

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: "value", color="track"
   :geom: geom_histogram()
   :layout: column-2
   :width: 300

   A histogram plot. Each track is plotted in a separate plot.

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: "value", color="track"
   :geom: geom_histogram() + facet_wrap("~track")
   :groupby: all
   :width: 300

   A histogram plot, but using the facet-wrap functionality
   of ggplot/plotnine.


.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: "value", color="track"
   :geom: geom_histogram() + facet_wrap("~track") + theme_xkcd()
   :groupby: all
   :width: 300

   A histogram plot, but using theming.


.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: "value", color="track"
   :geom: geom_histogram() + facet_wrap("~track") + theme_xkcd() + theme(figure_size=(20, 20))
   :groupby: all
   :width: 300

   A histogram plot, but using theming and setting the figure size
	   

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

