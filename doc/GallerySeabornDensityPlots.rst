.. _sb_kde_plot:

============
sb-kde-plot
============

The :class:`CGATReportPlugins.Seaborn.KdePlot` displays
:term:`numerical arrays` as a density using the kdeplot 
function from the seaborn_ package.


.. report:: Trackers.SingleColumnDataExample
   :render: sb-kde-plot
   :layout: row
   :width: 200

   A density-plot.

Options
-------

:class:`CGATReportPlugins.Seaborn.KdePlot` understands the
following options:

.. glossary::
   :sorted:

   kwargs
      string
      
      String with keyword arguments to the Seaborn kdeplot function.

.. report:: Trackers.SingleColumnDataExample
   :render: sb-kde-plot
   :layout: row
   :width: 200
   :kwargs: vertical=True

   A vertical density-plot.

.. _sb_dist_plot:

============
sb-dist-plot
============

The :class:`CGATReportPlugins.Seaborn.DistPlot` displays
:term:`numerical arrays` as a density using the distplot 
function from the seaborn_ package.


.. report:: Trackers.SingleColumnDataExample
   :render: sb-dist-plot
   :layout: row
   :width: 200

   A density-plot.

Options
-------

.. glossary::
   :sorted:

   kwargs
      string
      
      String with keyword arguments to the Seaborn distplot function.


.. report:: Trackers.SingleColumnDataExample
   :render: sb-dist-plot
   :layout: row
   :width: 200
   :kwargs: vertical=True

   A vertical density-plot
