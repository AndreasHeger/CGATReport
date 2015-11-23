.. _Tutorial7:

=================================
Adding active content
=================================

Per default, cgatreport`Sphinx` builds static documents. If the document
is rendered as html, active content can be added by running a 
web server.

.. note::
   Running a web server potentially opens security holes. Only
   run a web server if you know what you are doing. Also, do
   not assume that I know what I am doing.

cgatreport uses `web.py <http://webpy.org>`_ as a server.
Make sure it is installed. To test if it is, run::

   import web

from your python command line.

Active content can be added to the file :file:`server.py` in the 
root directory. Already available applications are

   * :class:`DataTable`

See :ref:`Configuration`, in particular the variable
:term:`cgatreport_urls` on how to enable these applications.

In order to start the web server, run::

   make server-start 

in the root directory of your document. See the :file:`Makefile`
for configuration options.

The document should now be accessible at ``http://localhost:8080/static/index.html``.

.. note::

   Contents of the cache can also be retrieved with the :ref:`cgatreport-get`
   command line utility.

