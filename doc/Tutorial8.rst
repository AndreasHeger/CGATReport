.. _Tutorial8:

==================================
Extending CGATReport
==================================

cgatreport can be extended via plugins.  Extension points are
available to add new Renderers and Transformers.

There is a quick-and-dirty way and a more principled way.

Simple extension
================

.. report:: Tracker.Empty
   :render: MyPlots.ExampleWithoutData

   An example of a plot that does not require data

Here, cgatreport can not match ``MyPlots.ExampleWithoutData``
with any of the known :term:`Renderers`. Instead, it will try to import
the function ``ExampleWithoutData`` from the module ``MyPlots``. The
latter should be somewhere within the :envvar:`PYTHONPATH`.

For better re-use, it is good practice to separate the data and the
rendering process.  The same plot with a :term:`Tracker` and a
:term:`Renderer`.

.. report:: MyPlots.ExampleData1
   :render: MyPlots.ExampleWithData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

As a benefit of this approach, the individual components can be re-used.
For example, a different dataset can be plotted in the same way:

.. report:: MyPlots.ExampleData2
   :render: MyPlots.ExampleWithData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

Writing plugins
===============

At some stage, a :term:`Renderer` has been refined to such an extent
that it has become generally useful and you want to add it to
cgatreport so that it becomes available in all reports. CGATReport
provides a plugin mechanism to do this.

.. note::
   The following section is not up-to-date.

Writing a transformer
---------------------

Let us say we want to create a new :term:`Transformer` for our CGAT
project. We will group them into a python module called
``MyCGATReportPlugins``. Conceptually we need to do things. We need
to provide the actual implemenation of the Transformer and we need to
tell the plugin system about the availability of the transformer.

Let us start with the following directory structure::

    .
    |-- MyCGATReportPlugins
    |   |-- CGATTransformer.py
    |   `-- __init__.py
    |-- ez_setup.py
    `-- setup.py

The new module contains the file ``CGATTransformer.py`` which contains
the code for our transformer::

    from CGATReportPlugins.Transformer import Transformer

    class TransformerCount(Transformer):
	'''Count the number of items on the top level of 
	the hierarchy.
	'''

	nlevels = 0

	def transform(self, data, path):
	    for v in data.keys():
		data[v] = len(data[v])
	    return data

The :attr:`nlevels` is used the by the :meth:`__call()__` method in
the :class:`CGATReportPlugins.Transformer` class to iterate over the
data tree at a certain level. Note that instead of overloading the
:meth:`transform` method, the :meth:`__call__()` method can be
overloaded to allow complete control over the DataTree.

The file ``__init__.py`` is empty and is simply required for our
module to be complete (and the ``setuptools.find_packages()`` function
to find our module).

Registering a plugin
--------------------

CGATReport uses the `setuptools <http://pypi.python.org/pypi/setuptools>`_
plugin architecture. A copy of the file :file:`ez_setup.py` is part of the
CGATReport installation, but can also be obtained from `here <http://peak.telecommunity.com/dist/ez_setup.py>`_.

The file :file:`setup.py` installs our plugin and at the same time
registers it with CGATReport::

    import ez_setup
    ez_setup.use_setuptools()

    from setuptools import setup, find_packages

    setup(name='MyCGATReportPlugins',
	  version='1.0',
	  description='CGATReport : CGAT plugins',
	  author='Andreas Heger',
	  author_email='andreas.heger@gmail.com',
	  packages=find_packages(),
	  package_dir = { 'MyCGATReportPlugins': 'MyCGATReportPlugins' },
	  keywords="report generator sphinx matplotlib sql",
	  long_description='CGATReport : CGAT plugins',
	  entry_points = \
	      {
		  'CGATReport.plugins': [
		'transform-count=MyCGATReportPlugins.CGATTransformer:TransformerCount',
		]
		  },
	  )

The registration happens at the ``entry_points`` option to
``setup``. The dictionary entry_points declares the presence of
plugins. Here, the line::

    'CGATReport.plugins': [
        'transform-count=MyCGATReportPlugins.CGATTransformer:TransformerCount',
    ]

tells the plugin system, that our class ``TransformerCount`` in the
module ``MyCGATReportPlugins.CGATTransformer`` is a plugin for
cgatreport. The plugin is called ``transform-count``, which is
automatically linked by cgatreport to ``:transform:``, such that the
following will now work::

   .. report:: Trackers.LabeledDataExample
      :render: table
      :transform: count

   Table with counts

Additional plugins can be added as additional items in the list.

See the :class:`CGATReportPlugins.Transformer` documentation for
existing transformer.

Writing Renderers
-----------------

A plugin for a :term:`Renderer` can be written in the same way as a
:term:`Transformer`. While the latter will receive data and return the
transformed data, a :term:`Renderer` receives data and returns a
representation of that data - a table, a plot, etc.

A :term:`renderer` returns a collection of
:class:`CGATReport.ResultBlocks`. A :term:`ResultBlock` contains the
restructured text that is inserted into the document at the point of
the ``report`` directive.

At the same time, a :term:`Renderer` can create plots on a variety of
devices. These plots will be collected by various agents of the
CGATReport framework and inserted into the document. In order to
associatde a plot with text, usually a place-holder is defined.

The following collectors are defined:

matplotlib plots
   ``#$mpl %i$#`` with ``%i`` being the current matplotlib figure id 

   Implemented in :class:`CGATReportPlugins.MatplotlibPlugin``

R plots
   ``#$rpl %i$#`` with ``%i`` being the current R device number

   Implemeted in :class:`CGATReportPlugins.RPlotPlugin``

HTML text
   ``#$html %s$#`` with ``%s`` being the :attr:`title` of the 
   :class:`CGATReport.ResultBlock`.

   Requires the :attr:`html` attribute to be defined in
    :class:`CGATReport.ResultBlock`. The contents
   are saved and a link is inserted in the text.

RST text
    Requires the ``text`` attribute to be defined in
    :class:`CGATReport.ResultBlock`. The contents are
    inserted into the document directly.

A simple implementation of a :term:`Renderer` using matplotlib could
be::

    from CGATReportPlugins.Renderer import Renderer
    from CGATReport import ResultBlock, ResultBlocks
    import matplotlib

    class ScatterPlot( Transformer ):
	'''print a scatter plot of multiple datasets.
	'''

	nlevels = 1

	def render(self, data, path):
	    plts = []
	    figid = plt.figure()

	    for label, coords in data.iteritems():
	        assert len(coords) >= 2
		k = coords.keys()
		xlabel = k[0]
		for ylabel in k[1:]:
		    xvals, yvals = coords[xlabel],coords[ylabel]
		    plt.scatter( xvals, yvals )

	    return ResultBlocks( ResultBlock( 
	                    '''#$mpl %i$#\n''' % figid,
			    title = 'ScatterPlot' ) )



This particular example is derived from the class
:class:`CGATReport.Renderer`. The base class implements a ``__call__``
method that calls the ``render`` functions at appropriate levels in
the data tree. However, there is no need for deriving from
:class:`CGATReport.Renderer`, the only requirement for your own
:term:`Renderer` is to implement a ``__call__( self, data)`` method.

Note that this simple example performs permits very little
customization such as setting axis labels, tick marks, etc.  The
various Rendereres that are implemented in CGATReport a part of a
class hierarchy that adds these customization options.

See the :class:`CGATReportPlugins.Renderer` documentation for existing
matplotlib renderers.



