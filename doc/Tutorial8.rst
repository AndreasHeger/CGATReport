.. _Tutorial8:

==================================
Tutorial 8: Extending SphinxReport
==================================

sphinxreport can be extended via plugins.
Extension points are available to add new
Renderers and Transformers.

There is a quick-and-dirty way and a more
principled way.

Quick and dirty extension
=========================

.. report:: Tracker.Empty
   :render: MyPlots.ExampleWithoutData

   An example of a plot that does not require data

Here, sphinxreport can not match ``MyPlots.ExampleWithoutData``
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

Writing plugins
===============

At some stage, a Renderer has been refined to such an extent
that it has become generally useful.

Let us say we want to create extensions for our CGAT project. We will
group them into a python module called
``CGATSphinxReportPlugins``. Conceptually we need to do things. We
need to provide the actual implemenation of the Transformer and we
need to tell the plugin system about the availability of the transformer.

Let us start with the following directory structure::

    .
    |-- CGATSphinxReportPlugins
    |   |-- CGATTransformer.py
    |   `-- __init__.py
    |-- ez_setup.py
    `-- setup.py

The new module contains the file ``CGATTransformer.py`` which contains
the code for our transformer::

    from SphinxReportPlugins.Transformer import Transformer

    class TransformerCount( Transformer ):
	'''Count the number of items on the top level of 
	the hierarchy.
	'''

	nlevels = 0

	def transform(self, data, path):
	    for v in data.keys():
		data[v] = len( data[v] )
	    return data

The :attr:`nlevels` is used the by the :meth:`__call()__` method in
the :class:`SphinxReportPlugins.Transformer` class to iterate over the data tree at a
certain level. Note that instead of overloading the :meth:`transform`
method, the :meth:`__call__()` method can be overloaded to allow
complete control over the DataTree.

The file ``__init__.py`` is empty and is simply required for our
module to be complete (and the ``setuptools.find_packages()`` function to find
our module).

Sphinxreport uses the `setuptools
<http://pypi.python.org/pypi/setuptools>`_
plugin architecture. A copy of the file :file:`ez_setup.py` is part of the
SphinxReport installation, but can also be obtained from `here <http://peak.telecommunity.com/dist/ez_setup.py>`_.

The file :file:`setup.py` installs our plugin and at the same time
registers it with SphinxReport::

    import ez_setup
    ez_setup.use_setuptools()

    from setuptools import setup, find_packages

    setup(name='CGATSphinxReportPlugins',
	  version='1.0',
	  description='SphinxReport : CGAT plugins',
	  author='Andreas Heger',
	  author_email='andreas.heger@gmail.com',
	  packages=find_packages(),
	  package_dir = { 'CGATSphinxReportPlugins': 'CGATSphinxReportPlugins' },
	  keywords="report generator sphinx matplotlib sql",
	  long_description='SphinxReport : CGAT plugins',
	  entry_points = \
	      {
		  'SphinxReport.plugins': [
		'transform-count=CGATSphinxReportPlugins.CGATTransformer:TransformerCount',
		]
		  },
	  )

The registration happens at the ``entry_points`` option to
``setup``. The dictionary entry_points declares the presence of
plugins. Here, the line::

    'SphinxReport.plugins': [
        'transform-count=CGATSphinxReportPlugins.CGATTransformer:TransformerCount',
    ]

tells the plugin system, that our class ``TransformerCount`` in the module
``CGATSphinxReportPlugins.CGATTransformer`` is a plugin for
sphinxreport. The plugin is called ``transform-count``, which is
automatically linked by sphinxreport to ``:transform:``, such that the following 
will now work::

   .. report:: Trackers.LabeledDataExample
      :render: table
      :transform: count

   Table with counts

Additional plugins can be added as additional items in the list.

See the :class:`SphinxReportPlugin.Transformer` documentation
for existing transformer.

See the :class:`SphinxReportPlugin.Renderer` documentation
for existing matplotlib renderers.
