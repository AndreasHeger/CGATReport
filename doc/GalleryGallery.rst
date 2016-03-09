.. _gallery:

=======
gallery
=======

:class:`CGATReportPlugins.Renderer.Gallery` renders a collection of image
files as returned by :class:`CGATReport.Tracker.TrackerImages`.

.. report:: Tracker.TrackerImages
   :render: gallery-plot
   :glob: images/*.png
   :layout: columns-2

   A collection of images

Options
-------

:class:`CGATReportPlugins.Renderer.Gallery` has no additional
options.


.. report:: Trackers.ImageOnly
   :render: gallery-plot
   :layout: columns-2

   A collection of images

.. report:: Trackers.ImageWithName
   :render: gallery-plot
   :layout: columns-2

   A collection of images
