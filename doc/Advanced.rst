.. _Advanced topics:

===============
Advanced topics
===============

This page collects a few advanced techniques for working with cgatreport.

User generated plots
====================

If the basic plots included in CGATReport are not enough (and there
is no reason why they shouldn't), plotting can be done within a tracker
while skipping the rendering step. See the :ref:`user` directive on
examples of using this.

Parameterizing cgatreport documents
=====================================

CGATReport documents can access configuration parameters in the
:file:`cgatreport.ini` file. For example, if
:file:`cgatreport.ini` contains the following section::

   [geneset]
   # genesets to report in the summary pages
   summary=abinitio,novel,lincrna,r(ref.*)

the variable ``geneset_summary`` can be used inside a :term:`report` directive::

   .. report:: Genemodels.GenesetSummary
      :render: table
      :tracks: @geneset_summary@

      Summary of gene sets

Conditional content
===================

The ifconfig_ extension allows to include content depending on configuration
values. To use this extension you will need to modify :file:`conf.py`.

Referring to other cgatreport documents
=========================================

The intersphinx_ extension permits referring to other
cgatreport documents. To use this extension, add the following to
your :file:`conf.py` configuration file::

    extensions = [ ..., 'sphinx.ext.intersphinx', ...]

    intersphinx_mapping = {'<identifier>': ('<path>', None) }

where identifier is a suitable identifier and ``path`` is the absolute
location of the html build of the sphinx document you want to refer
to. This directory should contain the :file:`objects.inv` file. The
file is automatically created by sphinx, but sphinx needs to be run at
least once.

To refer to the other documentation, type::

   :ref:`My link to another documentation <identifier:label>`

Where ``label`` needs to be a valid identifier in the referred to
document.

Using macros from another cgatreport document
===============================================

The intersphinx_ mechanism permits adding links to reports outside the
current report. However, it is also possible to use macros from
another cgatreport document directly in a document. This is possible
by specifying database locations within the ``report`` directive.  For
example, to show to tables from two different reports::

   .. report:: pipeline_docs.pipeline_mapping.trackers.MappingSummary
      :render: table
      :sql_backend: sqlite:///../mapping_sensitive/csvdb

      Mapping summary using sensitive mapping parameters

   .. report:: pipeline_docs.pipeline_mapping.trackers.MappingSummary
      :render: table
      :sql_backend: sqlite:///../mapping_strict/csvdb

      Mapping summary using strict mapping parameters

The path for ``sql_backend`` should be absolute or relative to the
directory from which the report is built.

The top of the hierarchy, ``pipeline_docs``, needs to be part of
``sys.path``, for example by adding it to the :file:`conf.py`
configuration file of the ``master`` document::

   sys.path.append("/path/to/mapping/code")

If ``sql_backend`` is not given, it defaults to the value
``report_sql_backend`` in the :file:`cgatreport.ini` configuration
file or if that is absent as well, to the sqlite database called
:file:`csvdb` in the current directory.

.. _intersphinx: http://sphinx-doc.org/ext/intersphinx.html
.. _ifconfig: http://sphinx-doc.org/ext/ifconfig.html
