.. _trackers:

========
Trackers
========

The purpose of a :term:`tracker` is to provide data for rendering.
As such, they need not follow strict rules - at minimum they
just need to callable and return a dictionary of values.
Users of cgatreport are encouraged to build their own
collection of :term:`trackers`.

However, cgatreport comes with a collection of :term:`trackers`
that cover some common use cases, in particular when working with
data organized in SQL databases. This section contains an overview 
of the trackers included in cgatreport. The use of the
:term:`trackers` here is optional.

Special purpose trackers
========================

.. toctree::
   :maxdepth: 2

   GalleryConfig.rst
   GalleryStatus.rst
   GalleryGallery.rst 
   TrackerSQL.rst

.. TrackerMultipleLists : needs to be renamed


