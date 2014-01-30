.. _Tutorial9:

==================================
Tutorial 9: Plotting with R
==================================

The principal plotting engine in SphinxReport is matplotlib. However,
it is just as easy to create plots with R. There are several ways
to use R for plotting: 

* :ref:`Via Plugins` extending the in-built plotting capabilities of SphinxReport,
* :ref:`Via Tracker` involving writing a :term:`Tracker` that both
  collects data and plots
* :ref:`Via ggplot2` involving a data frame and the R ggplot library.
   
Note that plotting with R makes use of rpy2, the python interface to R.

.. _Via Plugins:

Via Plugins
===========

Sphinxreport contains a few renderers that make use of the standard R plotting
library, for example :ref:`r-box-plot` or
:ref:`r-smooth-scatter-plot` (see :ref:`Renderers` for a complete list).

.. _Via Tracker:

Via Tracker
===========

Any plot, including those using R, can be created by combining the
:ref:`user` renderer with a :term:`Tracker` that does the plotting.
The section about :ref:`UserCreatedPlots` contains a few examples.

.. _Via ggplot2:

Via ggplot2
===========

ggplot2_ is a plotting system for R, based on the grammar of
graphics. Plots are built from a :term:`data frame` by adding aesthetics
and geometries.

In order to plot with ggplot2_, the results of a :term:`Tracker`
need first be converted to a :term:`data frame` with the 
:ref:`toframe` transformer::

    .. report:: Tutorial5.ExpressionLevel
       :render: debug
       :transform: toframe
       
       Debugging

.. report:: Tutorial5.ExpressionLevel
   :render: debug
   :transform: toframe

   Debugging   
   
Plotting is then done with :ref:`r-ggplot`. This :term:`Renderer` 
requires a ``statement`` describing the plot aesthetics and geometry. 

The simple example below plots the data on a straight line. Note
how the :term:`slice` ``expression`` is set as a column name in
the data frame and can thus be used within the ggplot statement::

    .. report:: Tutorial5.ExpressionLevel
       :transform: toframe
       :render: r-ggplot
       :statement: aes(expression, expression) + geom_point()
       :layout: column-2

       A simple plot

.. report:: Tutorial5.ExpressionLevel
   :transform: toframe
   :render: r-ggplot
   :statement: aes(expression, expression) + geom_point()
   :layout: column-2

   A simple plot

More interesting might be to plot a histogram::

    .. report:: Tutorial5.ExpressionLevel
       :render: r-ggplot
       :transform: toframe
       :statement: aes(expression) + geom_histogram()
       :layout: column-2

       A histogram plot

.. report:: Tutorial5.ExpressionLevel
   :render: r-ggplot
   :transform: toframe
   :statement: aes(expression) + geom_histogram()
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
       :render: r-ggplot
       :statement: aes(experiment1,experiment2) + geom_point()

       Correlation with expression values

.. report:: Tutorial9.ExpressionLevels
   :render: r-ggplot
   :statement: aes(experiment1,experiment2) + geom_point()

   Correlation with expression values
   	       
More interesting is to colour the different expression values by gene_function::

    .. report:: Tutorial9.ExpressionLevels
       :render: r-ggplot
       :statement: aes(experiment1, experiment2, color=factor(gene_function)) + geom_point()

       Correlation with expression values coloured by factor gene_function

.. report:: Tutorial9.ExpressionLevels
   :render: r-ggplot
   :statement: aes(experiment1, experiment2, color=factor(gene_function)) + geom_point()

   Correlation with expression values coloured by factor gene_function

The MeltedDataFrameTracker provides a shortcut::

    class MeltedExpressionLevels(MeltedTableTrackerDataframe):
        pattern = "(.*)_data"

The data is now in a single melted data frame with a column called
``track`` denoting the different tracks:

    .. report:: Tutorial9.MeltedExpressionLevels
       :render: r-ggplot
       :statement: aes(expression, color=factor(track)) + geom_density()

       Plot of gene expression densities

.. report:: Tutorial9.MeltedExpressionLevels
    :render: r-ggplot
    :statement: aes(expression, color=factor(track)) + geom_density()

    Plot of gene expression densities


See options in :ref:`sphinxreport-test` for ways to do interactive 
refinement of such plots.

.. note:: 
   Plotting from a mixture of SQL, R and python is powerful,
   but can sometimes be tricky when mapping SQL column names
   to data frame column names for use in ggplot descriptions. 
   Make sure to use long and unambiguous names that will not 
   give rise to name conflicts with built-in names in R,
   python and SQL.


