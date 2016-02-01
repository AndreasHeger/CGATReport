.. _Roadmap:

=======
Roadmap
=======

Planned features
================

The following features are planned:

latex/pdf
   test latex/pdf rendering of documents

add automatic history
    keep automatic track of releases/versions of
    the document.

examine memory usage
    large datasets require a large amount of memory,
    investigate if this can be optimized, for example
    by using numpy more efficiently

upload
    add upload to galaxy and/or UCSC

optional pdf support
    pdf rendering takes a while and could be post-poned until
    final document is produced. Similarly, pdf scatter plots 
    with many points take a long while to render and these should
    be thinned.

.. _Releases:

=============
Release Notes
=============

Version 0.3
===========

Numerous changes and bugfixes, such as:
 
* ipython notebook integration
* switch to pandas dataframes for data manipulation

Version 0.2.1
=============

* Removed bokeh dependency

Version 0.2
===========

* Complete feature implementation of the most popular
  Renderers and Transformers.

Version 0.1
===========

* Refactoring to use pandas_ dataframes for transformation
  and grouping.
* Some backwards-incompatible changes, thus rename project
  to CGATReport and give version number 0.1. Most trackers
  will need no or little changes, but custom Renderers or
  Transformers will need to be updated.

  Most notable backwards incompatible changes are:

  * default grouping is by track
  * several transformers deprecated as they are
    not needed any more

Version 2.4.1
=============

* Add javascript interactivity to plots using mpld3
* installation bugfix

Version 2.4.0
=============

* ?

Version 2.3
============

* Moved to github
* Use pandas_ dataframes for rendering
* Use seaborn_ plot aesthetics and plots
* Refined notebook integration
* r-ggplot now plots without needing X
* ggplot_ added
* pep8 reformatting
* added xls-table, rst-table, glossary-table
* TrackerImages requires :glob: attribute

Version 2.2
============

* Moved to setuptools 
* MeltedTableTracker and MeltedTableTrackerDataframe
* Added interactive plotting support via python/ipython console or
     ipython notebook   


Version 2.1
============

* Added Ian Sudbery's genelist tools
* Require matplotlib 1.2.1 for tight_layout() option.
* Call tight_layout() after each plot.
* added :add-percent: option to tables.

Version 2.0
===========

Python 3 compatibility and many features. Python 2.6 is not
supported any more as the rpy2 module is not available for
2.6.

Python3 support is incomplete, the following will not work:
* eps rendering - segmentation fault
* scipy.stats - can't be imported
* web.py - pip install fails

Version 1.2
===========

rpy integration
    R Plotting is now possible with the RPlot Plugin.

plugin architecture
    A plugin architecture has been added to allow easy
    extension of cgatreport with additional renderes,
    transformers and plotting engines.

data download
   data from cache can be retrieved via the cgatreport-get
   utility

web server
   cgatreport-server has been added to serve a report 
   and add interactive components.

refactoring
   Trackers can now provide tracks, slices or paths as properties
   in addition to functions resulting in cleaner syntax.

Version 1.1
===========

The following features have been added in version 1.1

Completed features
------------------

error bars
   added error bars to bar plots

colored scatter plotter
   add individual coloring option for dots in a 
   scatter plot

load balancing
    achieve better load balancing between processes instead
    of giving each process a fixed amount of work no matter
    how long it will take.

logging
    added summary of logging messages to ``cgatreport-build``.

multi-figure layout
   implemented multi-figure layout using option
   :layout: <>, where <> is column(default), row or grid.

added mpl-* options
   for fine-tuning plots, matplotlib configuration options
   can be set on a per-plot basis.

clean
   also remove files in _build/html/_sources and _doctrees
   that match to trackers.

multiprocessing
   better exception handling

test
   better output of available trackers - remove all
   objects that are not trackers.

windows compatibility
    check windows installation process and usage.
    Works in windows XP with python xy.

explorer output
    check output on windows explorer - frames do not appear on
    Chris' machine. Works on Windows XP, IE 8.

datatypes
   The nomenclature of datatypes was non-intuitive. Did away with 
   it and had each Renderer test for correctly formatted input.

add hinton plot
   added hinton plot (see http://www.scipy.org/Cookbook/Matplotlib)

--force option
   add --clean or --force option to cgatreport-test or build
   automatically force a new build. See also the corresponding
   sphinx-build options.

changed API
   changed model to use Dispatcher, Renderer and Transformer
   to disentangle figuring what to plot, plotting and data 
   transformation.

exceptions
   exceptions in trackers and renderers are added as .. warning
   blocks.

Known problems
--------------

matrix plot legend
   fix long legend text for matrix plots. The size of the legend
   is too small.

legend
   fix dimensioning of outer legend. Maybe add a separate
   legend plot.


