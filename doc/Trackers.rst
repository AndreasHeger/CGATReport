.. _trackers:

========
Trackers
========

The section contains an overview of all the trackers that are included
in sphinxreport.

Special purpose trackers
========================

.. toctree::
   :maxdepth: 2

   GalleryConfig.rst
   GalleryStatus.rst
   GalleryGallery.rst   

Accessing SQL tables
====================

Very often, sphinxreport is used to display data from an SQL database.
This section describes a set of utility trackers that permit easy
retrieval from SQL databases.

The basic tracker is called :class:`Tracker.TrackerSQL`. See
:ref:`Tutorial5` for an example using it. Following here is a more 
general description.

:class:`Tracker.TrackerSQL` is usually used by subclassing. It 
provides tracks that correspond to tables in the database matching a
certain pattern. For example, given the tables
``experiment1_results``, ``experiment1_data``,
``experiment2_results``, ``experiment2_data``,



 and overwriting
some attributes. The attributes are:

* :attr:`Tracker.TrackerSQL.pattern` - a regular expression 

 :class:`TrackerSQL`


