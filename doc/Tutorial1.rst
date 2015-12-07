.. _Tutorial1:

***********************
Starting a report
***********************

This first tutorial shows step-by-step how a new plot
can be added to a restructured text document.

=============================
Creating the skeleton project
=============================

First, we create a skeleton report in the directory tutorial::

   cgatreport-quickstart -d tutorial

This will create a skeleton report layout in the directory :file:`tutorial`.
Enter this directory and build the report as html::

   make html

This will create the skeleton report. View it by opening the file 
:file:`tutorial/_build/html/index.html` in a web browser.

==============
Adding a graph
==============

In this tutorial, will insert a simple bar plot into a restructured text document.
There are three steps involved:

1. Define a data source
2. Test the data source
3. Insert ``report`` directive in document

Adding a data source
====================

Create the file :file:`Tutorial1.py` in the :file:`trackers`
subdirectory and add the following code:

.. literalinclude:: trackers/Tutorial1.py
   :pyobject: MyDataFunction

This function returns an ordered dictionary with labeled
values.

Testing the data source
=======================

The utility :file:`cgatreport-test` can be used to check if a
data source works. To test your data source, type::

   cgatreport-test -t MyDataFunction -r bar-plot

on the command prompt in the root directory. This should create a 
bar plot (``-r bar-plot`` or ``--renderer=bar-plot`` ) of your data source
(``-t MyDataFunction`` or ``--tracker=MyDataFunction``).

:file:`cgatreport-test` will also produce the restructured text
required to render this graph within a restructured text document.
This utility is very useful for fine-tuning the appearance
of a plot before inserting it into the main document.

Creating a restructured text document
=====================================

Create the following rst file:`Tutorial1.rst`:

.. literalinclude:: Tutorial1Demo.rst

The :term:`report` directive is used to insert the graph into the
restructured text document. Behind the scenes, cgatreport`sphinx` will
call the cgatreport extension and request a barplot. The cgatreport in
turn will look for a data source :meth:`MyDataFunction` in the module
:file:`Tutorial1.py` that should be somewhere in your
:env:`PYTHONPATH` or added in :file:`conf.py`.  

.. note:: 
   `Tutorial1.py` or `MyDataFunction` are python module and function
   names and are thus case sensitive.

The default location for these is in the :file:`python` subdirectory
under the main installation directory. The content of the
:term:`report` directive is the figure or table caption.

Add a link in the :file:`contents.rst` by adding our newly created
page to the table of contents::

to make it look like::

   .. toctree::
      :maxdepth: 2

      Tutorial1.rst

and rebuild the sources::

    make html

There should now be a tutorial1 section in your document 
with a barplot. See :ref:`Tutorial1Demo` how it should look
like.

The next Tutorial (:ref:`Tutorial2`) will cover more complex
data sources and plots.





