.. _table:

=====
table
=====

The :class:`CGATReportPlugins.Renderer.Table` renders :term:`labeled
values` as a table.

Tables are built from columns and rows. By default, each :term:`slice`
creates a new table with each :term:`track` displayed in a row in a
table.  Columns are created from entries in the nested dictionary
returned by the tracker.

.. report:: Trackers.LabeledDataExample
   :render: table

   The default table.

Tables can display most data types and are the most versatile
of all renderers.

Options
-------

:class:`CGATReportPlugions.Renderer.Table` permits the following options:

.. glossary::

   transpose
      flag

      switch columns and rows.

   force
      flag

      show table, even if it is very large. By default, large
      tables are displayed in a separate page and only a link
      is inserted into the document.

   max-rows
      int
      
      Number of rows to display. If the table contains more rows,
      only a preview is created and the table is stored in an
      alternative format (see :attr:`large`),

   max-cols
      int
      
      Number of columns to display. If the table contains more columns,
      only a preview is created and the table is stored in an
      alternative format (see :attr:`large`),

   large
      choice

      Display large tables in alternate format. Possible formats are:
      ``html`` (defaul) for an html-formatted table and ``xls`` for
      an excel spreadsheet.

   add-percent
      string
   
      add a percentage column to a table. The format of this option is:
      ```column[,total]``. ``column`` denotes the column (usually a
      :term:`slice`) for which a percentage should be added. The
      optional argument ``total`` specifies the total to use. The
      total can be another column in the table or a value. If nothing
      is specified, the ``sum`` of all values in the column is used 
      to compute a total.

      Multiple columns can be added using a ``;`` separator.	    

      See :ref:`matrix` if you want to normalize across rows or
      columns across a table.

   format-columns
      string

      pretty format columns. Without option or if ``auto``, all
      columns will be auto-formated. Otherwise, the option takes a
      list column names separated by ``,``.
      
Formatting tables
-----------------

.. report:: Trackers.TableDataExample
   :render: table

   Unformatted table

.. report:: Trackers.TableDataExample
   :render: table
   :format-columns:

   Auto formatted table

.. report:: Trackers.TableDataExample
   :render: table
   :format-columns: bigint, bigfloat

   Selected columns formatted
      
Grouping tables
---------------

Using the generic :term:`groupby` option, tables can be re-organized differently.

For example, the table can be grouped by :term:`track` instead of
:term:`slice`:

.. report:: Trackers.LabeledDataExample
   :render: table
   :groupby: track

   Grouping by track

Alternatively, the table can be groupeb by :term:`track` and 
:term:`slice` creating a single table:

.. report:: Trackers.LabeledDataExample
   :render: table
   :groupby: all

   Grouping everything into a single table

Large tables
------------

.. report:: TestCases.MultiLevelTable
   :render: table

   Rendering a multi-level table

.. report:: TestCases.LargeTable
   :render: table

   Rendering a large table (as html)

.. report:: TestCases.LargeTable
   :render: table
   :large: xls

   Rendering a large table (as xls)

A table with images

.. report:: Trackers.DataWithImagesExample
   :render: table

   The default table.

Tables can display most data types and are the most versatile
of all renderers.

Adding percent
--------------

With the :term:`add-percent` option, percentage columns can be added
to a table. The percentage is added after the column chosen.

For example::

   .. report:: Trackers.LabeledDataExample
      :render: table
      :add-percent: column1

      Add a percent column

.. report:: Trackers.LabeledDataExample
   :render: table
   :add-percent: column1

   Add a percent column

The default is to use the column sum to compute the percentages.
Alternatives can be

* another column such as ``:add-percent:column1,column2``, or
* a value such as ``:add-percent:column1,20``.

Transposing
-----------

With the option :term:`transpose` option the rows and colums
of a table are switched.

For example::

   .. report:: Trackers.LabeledDataExample
      :render: table
      :transpose: 

      A transposed table

.. report:: Trackers.LabeledDataExample
   :render: table
   :transpose:

   A transposed table

=========
rst-table
=========

The :class:`CGATReportPlugins.Renderer.RSTTable` renders
:term:`labeled values` as a table in rst format

.. report:: Trackers.LabeledDataExample
   :render: rst-table

   RST tables

=========
xls-table
=========

The :class:`CGATReportPlugins.Renderer.XlsTable` renders :term:`labeled
values` as a table in xls format to download

.. report:: Trackers.LabeledDataExample
   :render: xls-table

   XLS Tables

The following is an example of XLS tables with a hierarchical
index

.. report:: Trackers.HierarchicalLabeledDataExample
   :render: xls-table

   XLS Tables

==========
html-table
==========

The :class:`CGATReportPlugins.Renderer.HtmlTable` renders
:term:`labeled values` as a table in html format to download

.. report:: Trackers.LabeledDataExample
   :render: html-table

   HTML Tables

=========
glossary
=========

The :class:`CGATReportPlugins.Renderer.GlossaryTable` renders :term:`labeled
values` as a table as a glossary

.. report:: Trackers.LabeledDataExample
   :render: glossary-table

   A glossary table
