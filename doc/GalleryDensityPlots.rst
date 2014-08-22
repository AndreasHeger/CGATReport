============
density-plot
============

The :class:`CGATReportPlugins.Plotter.DensityPlot` displays
:term:`numerical arrays` as a density using the kdeplot 
function from the seaborn_ package.


.. report:: Trackers.SingleColumnDataExample
   :render: density-plot
   :layout: row
   :width: 200

   A density-plot.

Options
-------

:class:`CGATReportPlugins.Plotter.DensityPlot` understands the
following options, for more information, see the documentation of
the seaborn package.

.. glossary::
   :sorted:

   shade
      flag

      If true, shade in the area under the KDE curve (or draw with
      filled contours when data is bivariate).

   vertical
      flag

      If True, density is on x-axis.

   kernel
      choice
    
      gau | cos | biw | epa | tri | triw.

      Code for shape of kernel to fit with. Bivariate KDE can only use
      gaussian kernel.

   bw 
      choice
      
      scott | silverman | scalar | pair of scalars

      Name of reference method to determine kernel size, scalar factor,
      or scalar for each dimension of the bivariate plot

   gridsize 
      int

      Number of discrete points in the evaluation grid.

   cut
      int

      Draw the estimate to cut * bw from the extreme data points.

   clip
      pair of scalars

      Lower and upper bounds for datapoints used to fit KDE


.. report:: Trackers.SingleColumnDataExample
   :render: density-plot
   :layout: row
   :width: 200
   :vertical:

   A vertical density-plot.
