.. _Tutorial4:

========================
Using slices
========================

Functors of type :class:`Tracker` can provide subsets of tracks. Each subset is a :term:`slice`.
This tutorial builds on the :class:`WordCounter` example from the previous tutorial.

*************
Adding slices
*************

In the :class:`WordCounter` example, let us say we want to examine the length of words starting with vocals (``AEIOU``) 
compared to those starting with consonants. One possibility is to extend the :attr:`tracks` attribute to
return new tracks like .py_vocals, .py_consonants, etc. This can easily become cumbersome. A better way 
to do this is to use slices. 

Add the following code to :file:`Tutorial4.py`:

.. literalinclude:: trackers/Tutorial4.py

This counter again counts word sizes in ``.py`` and ``.rst`` files,
but collects counts separately for words starting with vocals and
consonants. What is counted is determined by the ``slice`` option.
cgatreport will query the :attr:`slices` attribute and then call the
Tracker with all combinations of :term:`tracks` and :term:`slices`.

Testing the data source::

   cgatreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5

will now produce three plots, one for each :term:`track`. Per default,
plots are grouped by ``track``, but the grouping can be changed using
the option ``groupby=slice``::

   cgatreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o groubpy=slice

Again, three plots are created, but this time there is one plot per
``track``.

Which :term:`tracks` and :term:`slices` are plotted can be controlled
through options, too. To select only one or more :term:`tracks`, use
the ``-o tracks=track[,...[,...]]`` option::

   cgatreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o tracks=.py

To select one or more :term:`slices`, use the ``-o
slices=slice[,...[,...]]`` option::

   cgatreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o slices=vocals,consonants

****************************************************
Inserting the graphs in a restructured text document
****************************************************

We can now add these three plots into a restructured text document using
a single report directive block:

.. literalinclude:: Tutorial4Demo.rst
   :lines: 10-16

Additionally you can add the plots grouped by slices:

.. literalinclude:: Tutorial4Demo.rst
   :lines: 20-27

More fine grained control is possible. The following only shows a
single plot:

.. literalinclude:: Tutorial4Demo.rst
   :lines: 31-40

See :ref:`Tutorial4Demo` to check how the result should look like.


