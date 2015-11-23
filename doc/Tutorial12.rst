.. _Tutorial12:

=================================
Plotting with ggplot
=================================

..
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
	  :aes: 'value' 
	  :geom: geom_histogram()

	  A simple histogram plot

   .. report:: Tutorial5.ExpressionLevel
      :render: ggplot
      :aes: 'value', 
      :geom: geom_histogram()
      :layout: column-2
      :width: 300

      A simple histogram plot

   If we want to display multiple data sets on the same plot, the data
   needs to be grouped::

       .. report:: Tutorial5.ExpressionLevel
	  :render: ggplot
	  :aes: 'value' 
	  :geom: geom_histogram()
	  :groupby: all

	  A histogram plot

   .. report:: Tutorial5.ExpressionLevel
      :render: ggplot
      :aes: 'value' 
      :geom: geom_histogram()
      :groupby: all
      :width: 300

      A histogram plot

   We can also colour by :term:`track`::

       .. report:: Tutorial5.ExpressionLevel
	  :render: ggplot
	  :aes: 'value', color='track'
	  :geom: geom_histogram()
	  :groupby: all
	  :width: 300

	  A histogram plot

   .. report:: Tutorial5.ExpressionLevel
      :render: ggplot
      :aes: 'value', color='track'
      :geom: geom_histogram()
      :groupby: all
      :width: 300

      A histogram plot

   Creating a data frame from an SQL statement is a common use case. Say
   we want to create a plot with the correlation of expression values
   between two experiments. We implement the following :term:`tracker`
   that returns a :term:`data frame`:

   .. literalinclude:: trackers/Tutorial9.py

   Note how the data is arranged differently to the previous example::

   .. report:: Tutorial9.ExpressionLevels
      :render: dataframe
      :head: 10
      :tail: 10

   Plotting can be done thus::

       .. report:: Tutorial9.ExpressionLevels
	  :render: ggplot
	  :aes: 'experiment1','experiment2' 
	  :geom: geom_point()

	  Correlation with expression values

   .. report:: Tutorial9.ExpressionLevels
      :render: ggplot
      :aes: 'experiment1','experiment2' 
      :geom: geom_point()
      :width: 300

      Correlation with expression values

   More interesting is to colour the different expression values by
   gene_function::

       .. report:: Tutorial9.ExpressionLevels
	  :render: ggplot
	  :aes: 'experiment1', 'experiment2', color='gene_function'
	  :geom: geom_point()

	  Correlation with expression values coloured by factor gene_function

   .. report:: Tutorial9.ExpressionLevels
      :render: ggplot
      :aes: 'experiment1', 'experiment2', color='gene_function'
      :geom: geom_point()
      :width: 300

      Correlation with expression values coloured by factor gene_function

   See options in :ref:`cgatreport-test` for ways to do interactive
   refinement of such plots.

