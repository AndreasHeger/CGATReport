.. _Roadmap:

=======
Roadmap
=======

Planned features
================

The following features are planned:

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
    investigate if this can be optimized.

windows compatibility
    check windows installation process and compatibility.

load balancing:
    achieve better load balancing between processes instead
    of giving each process a fixed amount of work no matter
    how long it will take.

plugin architecture
    Clean up Renderer.py so that adding custom renderers
    will become easy. Consider adding a generic interface
    to matplotlib plotting functions.

upload
    Add upload to galaxy and/or UCSC

rpy integration
    Check if it is possible to use rpy as rendering engine and
    for more statistical tests.

--force option
    add --clean or --force option to sphinxreport-test or build
    automatically force a new build 

explorer output
    check output on windows explorer - frames do not appear on
    Chris' machine.


Completed features
==================


