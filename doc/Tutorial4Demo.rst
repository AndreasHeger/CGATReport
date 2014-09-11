.. _Tutorial4Demo:

==========
Tutorial 4
==========

Using slices
============

.. report:: Tutorial4.WordCounterWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,1

   Word sizes in .py and .rst files. 

Using tracks
============

.. report:: Tutorial4.WordCounterWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,1
   :groupby: track

   Word sizes in .py and .rst files. 

Selecting tracks and slices
===========================

.. report:: Tutorial4.WordCounterWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,1
   :tracks: .py,.rst
   :slices: vocals

   Word sizes of words starting with vocals in .py and
   .rst files.
