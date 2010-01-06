.. _Tutorial4:

========================
Tutorial 4: Using slices
========================

Functors of type :class:`Tracker` can provide subsets of tracks. Each subset is a :term:`slice`.
This tutorial builds on the :class:`WordCounter` example from the previous tutorial.

*************
Adding slices
*************

In the :class:`WordCounter` example, let us say we want to examine the length of words starting with vocals (``AEIOU``) 
compared to those starting with consonants. One possibility is to extend the :meth:`getTracks()` method to
return new tracks like .py_vocals, .py_consonants, etc. This can easily become cumbersome. A better way 
to do this is to use slices. 

Add the following code to :file:`Tutorial3.py`::

    class WordCounterWithSlices(Tracker):
	"""Counting word size."""

	def getTracks( self, subset = None ):
	    return ( "all", ".py", ".rst" )

	def getSlices( self, subset = None ):
	    return ( "all", "vocals", "consonants")

	def __call__(self, track, slice = None ):
	    word_sizes = []

	    if track == "all" or track == None:
		tracks = [ ".py", ".rst" ]
	    else:
		tracks = [track]

	    if slice == "all" or slice == None:
		test_f = lambda x: True
	    elif slice == "vocals":
		test_f = lambda x: x[0].upper() in "AEIOU"
	    elif slice == "consonants":
		test_f = lambda x: x[0].upper() not in "BCDFGHJKLMNPQRSTVWXYZ"

	    for root, dirs, files in os.walk('.'):
		for f in files:
		    fn, ext = os.path.splitext( f )
		    if ext not in tracks: continue
		    infile = open(os.path.join( root, f),"r")
		    words = [ w for w in re.split("\s+", "".join(infile.readlines())) if len(w) > 0]
		    word_sizes.extend( [ len(w) for w in words if test_f(w)] )
		    infile.close()

	    return { "word sizes" : word_sizes }

This counter again counts word sizes in ``.py`` and ``.rst`` files, but collects counts separately
for words starting with vocals and consonants. What is counted is determined by the ``slice`` option.
:mod:`SphinxReport` will call the :meth:`getSlices` method and then call the Tracker with all combinations
of :term:`tracks` and :term:`slices`.

Testing the data source::

   sphinxreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5

will now produce three plots, one for each slice. Per default, plots are grouped by ``slice``, but the grouping
can be changed using the option ``groupby=track``::

   sphinxreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o groubpy=track

Again, three plots are created, but this time there is one plot per ``track``. 

Which :term:`tracks` and :term:`slices` are plotted can be controlled through options, too. To select only
one or more :term:`tracks`, use the ``-o tracks=track[,...[,...]]`` option::

   sphinxreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o tracks=.py

To select one or more :term:`slices`, use the ``-o slices=slice[,...[,...]]`` option::

   sphinxreport-test -t WordCounterWithSlices -r line-plot -m histogram -o range=0,100,5 -o slices=vocals,consonants

****************************************************
Inserting the graphs in a restructured text document
****************************************************

We can now add these three plots into a restructured text document using
a single report directive block::

    ==========
    Tutorial 4
    ==========

    Using slices

    .. report:: Tutorial3.WordCounterWithSlices
       :render: histogram-plot
       :tf-range: 0,100,1

       Word sizes in .py and .rst files grouped by slice

Additionally you can add the plots grouped by tracks::

    .. report:: Tutorial3.WordCounterWithSlices
       :render: histogram-plot
       :tf-range: 0,100,1
       :groupby: track

       Word sizes in .py and .rst files grouped
       by track.

More fine grained control is possible. The following only shows a single plot::

    .. report:: Tutorial3.WordCounterWithSlices
       :render: histogram-plot
       :tf-range: 0,100,1
       :tracks: .py,.rst
       :slices: vocals

       Word sizes of words starting with vocals in .py and
       .rst files.

See :ref:`Tutorial4Demo` to check how the result should look like.


