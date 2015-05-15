.. _slideshow-plot:

==============
slideshow-plot
==============

:class:`CGATReportPlugins.SlideShow.SlideShowPlot` renders a
collection of image files as a gallery. Note that this
:term:`Renderer` requires the jssor_ javascript library to included in
the sphinx_ theme.


.. report:: Tracker.TrackerImages
   :render: slideshow-plot
   :glob: images/*.jpg

   A collection of images

Images are resized to fit into a given display size. To view the
original image, right-click in your browser and open the image.

Options
-------

:class:`CGATReportPlugins.Renderer.SlideShowSlideShowPlot` understands
       the following options:
       
.. glossary::
   :sorted:

   autoplay
      flag

      If set, the slide show will auto-play.

   style
      string

      Slide show style. Possible values are 
      * plain: only image
      * caption: slide show with image captions
      * thumbnail-navigator: slide show a thumbnail navigator

   thumbnail-display
      int
 
      Number of thumbnails to display in thumbnail navigator

   thumbnail-lanes
      int
 
      Number of thumbnail lanes to display in thumbnail navigator

   thumbnail-width
      int

      Width of the thumbnail navigator in pixels.

Styles
-------

A slide show with captions underneath the images.

.. report:: Tracker.TrackerImages
   :render: slideshow-plot
   :style: caption
   :glob: images/*.jpg

   A collection of images with captions

.. report:: Tracker.TrackerImages
   :render: slideshow-plot
   :style: thumbnail-navigator
   :glob: images/*.jpg
   :thumbnail-display: 5
   :thumbnail-lanes: 2
   :thumbnail-width: 200

   A collection of images with thumbnail navigator

Testing
-------

Setting the size of the slide show and starting autoplay:

.. report:: Tracker.TrackerImages
   :render: slideshow-plot
   :glob: images/*.jpg
   :width: 400
   :height: 200
   :autoplay:

   A collection of images

