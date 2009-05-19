.. _Introduction:

************
Introduction
************

The :mod:`SphinxReport` module is an extension for :mod:`sphinx`
that provides facilities for data retrieval and data rendering
within reStructured text. 

.. _Installation:

Installation
************

In order to install the extension, download the latest sources from *TODO*
or check out the latest code from svn (*TODO*).

To install, type::

   python setup.py build
   python setup.py install

First steps
***********

To get running quickly, use the the :file:`sphinxreport-quickstart.py`` to
create a skeleton project in the directory ``newproject``::

   sphinxreport-quickstart.py -d newproject

Enter ``newproject`` and build the skeleton report::

   make html

Open :file:`newproject/_build/html/index.html` in your browser 
to view the skeleton documentation. 

At this stage you can review :ref:`Configuration`_ options
in the file :file:`conf.py` and then start adding content
to your report. See the :ref:`Tutorial` on how to do this.

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































