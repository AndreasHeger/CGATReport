.. _Roadmap:

=======
Roadmap
=======

Planned features
================

The following features are planned:

colored scatter plotter
   add individual coloring option for dots in a 
   scatter plot

error bars
   add error bars to bar plots and scatter plots

web server
   implement setting up and http server with web.py

latex/pdf
   test latex/pdf rendering of documents

data download
   add method to provide data from cache from the
   command line and possibly the web pages.

add error counst
    report the number of warnings and errors on the 
    sphinxreport-build output.

add automatic history
    keep automatic track of releases

add :as-percent: option
    display proportions optionally as percent

examine memory usage
    large datasets require a large amount of memory,
    investigate if this can be optimized, for example
    by using numpy more efficiently

windows compatibility
    check windows installation process and compatibility.

load balancing:
    achieve better load balancing between processes instead
    of giving each process a fixed amount of work no matter
    how long it will take.

plugin architecture
    clean up Renderer.py so that adding custom renderers
    will become easy. Consider adding a generic interface
    to matplotlib plotting functions.

upload
    add upload to galaxy and/or UCSC

rpy integration
    check if it is possible to use rpy as rendering engine and
    for statistical tests.

--force option
    add --clean or --force option to sphinxreport-test or build
    automatically force a new build. See also the corresponding
    sphinx-build options.

explorer output
    check output on windows explorer - frames do not appear on
    Chris' machine.

optional pdf support
    pdf rendering takes a while and could be post-poned until
    final document is produced. Similarly, pdf scatter plots 
    with many points take a long while to render and these should
    be thinned.

legend
   fix dimensioning of outer legend. Maybe add a separate
   legend plot.

multi-figure layout
   implement multi-figure layout using a new option
   :layout: <>, where <> is column(default), row or grid.

Completed features
==================


