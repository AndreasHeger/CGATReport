.. _Tutorial8:

==================================
Tutorial 8: Extending SphinxReport
==================================

:mod:`SphinxReport` can be extended via plugins.
Extension points are available to add new
Renderers and Transformers.

There is a quick-and-dirty way and a more
principled way.

Quick and dirty extension
=========================

.. report:: Tracker.Empty
   :render: MyPlots.ExampleWithoutData

   An example of a plot that does not require data

Here, :mod:`SphinxReport` can not match ``MyPlots.ExampleWithoutData``
with any of the known :term:`Renderers`. Instead, it will try to import
the function ``ExampleWithoutData`` from the module ``MyPlots``. The
latter should be somewhere within the :envvar:`PYTHONPATH`.

For better re-use, it is good practice to separate the data and the rendering process. 
The same plot with a :term:`Tracker` and a :term:`Renderer`.

.. report:: MyPlots.ExampleData1
   :render: MyPlots.ExampleWithoutData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

As a benefit of this approach, the individual components can be re-used.
For example, a different dataset can be plotted in the same way:

.. report:: MyPlots.ExampleData2
   :render: MyPlots.ExampleWithoutData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

Adding a new renderer as a plugin
=================================

At some stage, a Renderer has been refined to such an extent
that it has become generally useful.

In order to make a Renderer available
to :mod:`SphinxReport` it needs to be packaged.

TODO

See the :class:`SphinxReportPlugin.Renderer` documentation
for existing matplotlib renderers.

Additional transformers can be added in the same way.



