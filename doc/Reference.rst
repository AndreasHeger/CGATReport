.. _Reference:

*********
Reference
*********

This section contains a list of all renderes, trackers,
transformers and roles that are packaged with cgatreport.

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

    no-caption
      flag

      do not add the figure caption to the output.

    no-title
      flag

      do not plot title to the output.

    no-links
      flag

      do not output the link bar for a plot.

.. _Common plot options:

Common plot options
*******************

The following table lists common plotting options to the ``:render:``
directive. Not all will be having an effect, for example :term:`xtitle`
is only applicable to plots, but not tables. 

Superfluous options are ignored.

.. glossary::
   :sorted:

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

   function
      string

      add a function to a plot. The string given is evaluated on
      the current data range. Multiple functions can be separated
      by a ``,``. Some examples::

          :function: x       .. diagonal, y=x
	  :function: x**2    .. parabola, y=x**2
	  :function: 3       .. horizontal line at y=3
          :function: 3,6     .. two horizontal lines y=3 and y=6
	  :functien: math.sin(x)   .. sigmoid
      

   vline
      string
       
      add one or more horizontal lines to the plot. Coordinates are
      in graph coordinates. Multiple lines can be added as ','
      separated values. Some examples::

         :vline: 2             .. vertical line at x=2
	 :vline: 2,3           .. vertical line at x=2 and x=3     

   reverse-palette  
      flag

      reverse the color palette used for plotting matrices.

   plot-value  
      unchanged

   legend-location
      choice

      specify the location of the legend. See cgatreportmatplotlib
      for the basic options. Additional options are prefixed by ``outer``
      to place the legend outside a plot. Specify ``none`` to show no legend.
      The default option ``outer-top`` displays the legend above the plot. 

   xrange
      a pair of comma separate values

      restrict plot to part of the x-axis

   yrange
      a pair of comma separate values

      restrict plot to part of the y-axis

   zrange
      a pair of comma separate values

      restrict plot to part of the z-axis

   xformat      
      format of x ticks.

      In order to plot dates, prefix a date formatting string (see the
      python datetime module) with the prefix ``date=``. Using
      ``date`` on its own will use the default format, which should
      work in most cases.

   yformat
      format of y ticks.

      see :term:`xformat`

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

   format
      Image format of display image. The image format is a tuple 
      of the three items ``(<format>,<link>,<dpi>)``.

   extra-formats
      ``;`` separated list of extra image formats to generate. Extra
      formats are inserted as links below the default image.
      Each format is a tuple of the three items
      ``(<format>,<link>,<dpi>)``. For example, the following option
      will create two images, one hires png image and one svg image::

            :extra-formats: png,hires,200;svg,svg,100
      
   split-at
      non-negative int
       
      Split a figure after # graphical elements in order to avoid over-plotting.
      Different renderers have different defaults.       

   split-always
      list separated by comma

      Related to :term:`split-at`. If a plot is split into separate plots,
      the tracks given as argument will be added to each plot to facilitate
      comparisons.

