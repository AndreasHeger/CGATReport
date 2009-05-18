.. _Introduction:

************
Introduction
************

The :mod:`SphinxReport` module is an extension for :mod:`sphinx`
that provides facilities for data retrieval and data rendering
within reStructured text. 

.. _Configuration:

Configuration
*************

Sphinx and the :mod:`SphinxReport` extension read configuration details
from the file :file:`conf.py` at the top-level of the installation. In order
to use the extension, add the following entries to the variable :data:`extensions`::

   extensions.extend( ['SphinxReport.inheritance_diagram',
              'SphinxReport.only_directives',
              'SphinxReport.render_directive ] )

Further variables can be addded to :file:`conf.py` to customize the extension. The
variables are:

.. _Installation:

Installation
************

In order to install the extension, download the latest sources from *TODO*
or check out the latest code from svn (*TODO*).

To install, type::

   python setup.py build
   python setup.py install






























