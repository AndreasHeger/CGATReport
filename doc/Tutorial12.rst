.. _Tutorial12:

=================================
Tutorial 12: Plotting with ggplot
=================================

The :class:`SphinxReportPlugins.GGPlotter.GGPlot` displays
a dataframe using the python port (ggplot_) of the ggplot2_ package.

ggplot2_ is a plotting system for R, based on the grammar of
graphics. Plots are built from a :term:`data frame` by adding aesthetics
and geometries.

Plotting is that done with :ref:`ggplot`. This :term:`Renderer` 
requires two options, a statement describing the aesthetics and
a statement describing the geometry of the plot.

The simple example below plots the data on a straight line. Note
how the :term:`slice` ``expression`` is set as a column name in
the data frame and can thus be used within the ggplot statement::

    .. report:: Tutorial5.ExpressionLevel
       :render: ggplot
       :aes: 'experiment1', 'experiment2' 
       :geom: geom_point()

       A simple plot

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: 'experiment1', 'experiment2' 
   :geom: geom_point()

   A simple plot

More interesting might be to plot a histogram::

    .. report:: Tutorial5.ExpressionLevel
       :render: ggplot
       :aes: 'experiment1'
       :geom: geom_histogram()

       A histogram plot

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :aes: 'experiment1'
   :geom: geom_histogram()

   A histogram plot

If we want to display multiple data sets on the same plot, the data
needs to be melted::

    .. report:: Tutorial5.ExpressionLevel
       :render: ggplot
       :transform: melt
       :aes: 'Data', color='Track'
       :geom: geom_histogram()
       :layout: column-2

       A histogram plot

.. report:: Tutorial5.ExpressionLevel
   :render: ggplot
   :transform: melt
   :aes: 'Data', color='Track'
   :geom: geom_histogram()
   :layout: column-2

   A histogram plot

Creating a data frame from an SQL statement is a common use case. Say
we want to create a plot with the correlation of expression values
between two experiments. We implement the following :term:`tracker`
that returns a :term:`data frame` ::

    from SphinxReport.Tracker import *

    class ExpressionLevels(TrackerSQL):
	"""Expression level measurements."""

	def __call__(self, track ):
	    statement = """SELECT e1.expression AS experiment1, 
				e2.expression AS experiment2,
				e1.function as gene_function
				FROM experiment1_data as e1, 
				     experiment2_data as e2
				WHERE e1.gene_id = e2.gene_id"""

	    return self.getDataFrame( statement )

Plotting can then be done directly without transformation::

    .. report:: Tutorial9.ExpressionLevels
       :render: ggplot
       :aes: 'experiment1','experiment2' 
       :geom: geom_point()

       Correlation with expression values

.. report:: Tutorial9.ExpressionLevels
   :render: ggplot
   :aes: 'experiment1','experiment2' 
   :geom: geom_point()

   Correlation with expression values
   	       
More interesting is to colour the different expression values by gene_function::

    .. report:: Tutorial9.ExpressionLevels
       :render: ggplot
       :aes: 'experiment1', 'experiment2', color='gene_function'
       :geom: geom_point()

       Correlation with expression values coloured by factor gene_function

.. report:: Tutorial9.ExpressionLevels
   :render: ggplot
   :aes: 'experiment1', 'experiment2', color='gene_function'
   :geom: geom_point()

   Correlation with expression values coloured by factor gene_function

See options in :ref:`sphinxreport-test` for ways to do interactive 
refinement of such plots.

