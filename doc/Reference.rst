.. _Reference:

*********
Reference
*********

This section contains a list of all renderes, trackers,
transformers and roles that are packaged with sphinxreport.

To make best use of the examples, use  the
``Show Source`` link in the left navigation bar
and the ``[source code]`` access link next to each 
rendered macro.

.. toctree::
   :maxdepth: 2

   Renderers.rst
   Trackers.rst
   Transformations.rst
   Roles.rst
   Utilities.rst

.. _General report options:

General report options
**********************

The following table lists all generic options to the ``:render:``
directive. 

.. glossary::
   :sorted:

   groupby   
      choice of 'tracks', 'slices', 'all'

      defines the grouping order. If a tracker provides multiple slices
      and tracks, the grouping can be either tracks first ('tracks') or
      slices first ('slices'). If :term:`groupby` is 'all', all tracks
      and slices will be rendered together. The default is to group by
      'slices'.

   layout  
     choice of 'row', 'grid', 'column', 'column-#'

     control the layout of the rendered objects. By default, objects
     are entered into the page as a list (``column``). Other layout
     options arrange them in table either as a single row (``row``),
     multiple columns (``column-#`` where ``#`` is the number of
     columns) or as a grid (``grid``, equal number of rows and columns).

   tracks 
      list separated by comma

      tracks to output. The tracks available depend on the
      tracker. The default is to output all tracks. In the following
      Example, only the tracks 'set1' and 'set2' are output::

         :slices: set1,set2

   slices 
      list separated by comma

      slices to output. The slices available depend on the
      tracker. The default is to output all slices. In the following
      Example, only the slices 'all' and 'novel' are output::
         
         :slices: all,novel

   tracker
      string

      options for the tracker object. The :term:`tracker` must
      define and optional keyword argument options. Note that 
      using this option will bypass caching.

.. _Common plot options:

Common plot options
*******************

The following table lists common plotting options to the ``:render:``
directive. Not all will be having an effect, for example :term:`xtitle`
is only applicable to plots, but not tables. 

Superfluous options are ignored.

   logscale  
      choice of 'x', 'y', 'xy'

      convert x-axis, y-axis or both axes to logarithmic coordinates.

   title  
      string

      add a title to the plot

   xtitle  
      string

      add an explicit label to the X-axis. The default is to use the
      one supplied by the :class:Tracker.

   ytitle  
      string

      add an explicit label to the Y-axis. The default is to use the
      one supplied by the :class:Renderer.

   add-title
      flag

      add title within in each plot

   force
      flag

      force display of large tables and matrices. If given,
      the large table will be inserted. The default behaviour is to create
      a separate file for the table and link to it.

   reverse-palette  
      flag

      reverse the color palette used for plotting matrices.

   plot-value  
      unchanged

   legend-location
      choice

      specify the location of the legend. See sphinxreportmatplotlib for options. The default 
      option 'outer' displays the legend next to the plot.

   xrange
      a pair of comma separate values

      restrict plot to part of the x-axis

   yrange
      a pair of comma separate values

      restrict plot to part of the y-axis

   zrange
      a pair of comma separate values

      restrict plot to part of the z-axis

   mpl-figure
      ``;`` separated ``key=value`` pairs

      options for matplotlib ``figure`` calls().

   mpl-legend
      ``;`` separated ``key=value`` pairs   

      options for matplotlib ``legend`` calls().

   mpl-subplot
      ``;`` separated ``key=value`` pairs

      options for matplotlib ``subplots_adjust`` calls().

   mpl-rc
      ``;`` separated ``key=value`` pairs

      general environment settings for matplotlib.
      See the matplotlib documentation. Multiple options can be
      separated by ;, for example 
      ``:mpl-rc: figure.figsize=(20,10);legend.fontsize=4``


