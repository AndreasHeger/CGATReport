.. _Tutorial3:

===============================
 Tutorial 3: Using transformers
===============================

This tutorial introduces ``Transformers``. A :class:`Transformer` changes the
data from a :class:`Tracker` before it is passed to a :class:`Renderer` for plotting.
To illustrate their use we will count word sizes of ``.py`` and ``.rst`` files.

***********************
Creating a word counter
***********************

First we create a new data source that will count words. We will record
the counts separately in ``.py`` and ``.rst`` files.

Create the file :file:`Tutorial3.py` in the :file:`python` subdirectory and add 
the following code::

    from SphinxReport.Tracker import *

    import os

    class WordCounter(Tracker):
	"""Counting word size."""

	def getTracks( self, subset = None ):
	    return ( "all", ".py", ".rst" )

	def __call__(self, track, slice = None ):
	    word_sizes = []

	    if track == "all" or track == None:
		tracks = [ ".py", ".rst" ]
	    else:
		tracks = [track]

	    for root, dirs, files in os.walk('.'):
		for f in files:
		    fn, ext = os.path.splitext( f )
		    if ext not in tracks: continue
		    infile = open(os.path.join( root, f),"r")
		    words = re.split("\s+", "".join(infile.readlines()))
		    word_sizes.extend( [ len(word) for word in words ] )
		    infile.close()

	    return { "word sizes" : word_sizes }

This Tracker counts word sizes in ``.py``, ``.rst`` files in the current directory.
Note that the tracker again returns a dictionary. The dictionary contains one entry
(``word sizes``) with a list of word sizes.

We can look at the word sizes returned::

Testing this data source::

   sphinxreport-test -t WordCounter -r table 

The output is not very informative. :mod:`SphinxReport` contains methods (objects of the type :class:`Tranformer`) 
modify data before display. For example, the :class:`TransformerHistogram` computes a histogram (``-m histogram`` or
``--transformer=histogram``)::

   sphinxreport-test -t WordCounter -r table -m histogram

The array of word size is replaced with two arrays for bins and values. Again, the tabular output is not very informative. 
However, the histogram is easily plotted choosing a different :class:`Renderer`::

   sphinxreport-test -t WordCounter -r line-plot -m histogram

Most objects of type :class:`Renderer` or :class:`Transformer` accept options. Options are passed
with :file:`sphinxreport-test` with the ``-o arg=value`` or ``--option=arg=value`` syntax.
For example to compute the histogram in the range from 0 to 100 in steps of size 5 and to display the histogram 
as lines, we can specify:

   sphinxreport-test -t WordCounter -r line-plot -m histogram -o range=0,100,5 -o as-lines


****************************************************
Inserting the graphs in a restructured text document
****************************************************

We can now add the histogram into a restructured text document using
a single report directive block::

    ==========
    Tutorial 3
    ==========

    Plotting a histogram
    ====================

    .. report:: Tutorial3.WordCounter
       :render: line-plot
       :transform: histogram
       :tf-range: 0,100,1
       :as-lines:

       Word sizes in .py and .rst files. 

See :ref:`Tutorial3Demo` to check how the result should look like.
