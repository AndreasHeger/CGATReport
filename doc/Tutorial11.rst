.. _Tutorial11:

====================================
Plotting Venn diagrams
====================================

A simple example
----------------

To find the overlap between two transcription factors we define a
TrackerMultipleLists tracker, plot the venns and calculate the
p-values::

    class SimpleOverlap(TrackerMultipleLists):

       statements = {"AR": "SELECT gene_id FROM Promoters_with_ar",
                     "ERG": "SELECT gene_id FROM Promoters_with_erg",
                     "background":"SELECT gene_id FROM all_genes"}

And then we can render it as a venn diagram using the ``venn``
transformer and ``venn-plot`` renderer, or test the statistical
significance of the overlap using the ``hypergeometric`` transformer
and the ``table`` renderer.

As a venn:

.. report:: Genelists.SimpleOverlap
   :render: venn-plot
   :transform: venn

   A venn diagram of the overlap

As a table:

.. report:: Genelists.SimpleOverlap
   :render: table
   :transform: hypergeometric

   Statistics on the overlap.

But we can do so much more than this. I will now take you through a
fairly complex use case of this set of tools, and explain in more
detail what is going on.

The sitch
----------

I have used RNAseq to define a set of differentially expressed genes
in some experiment. I also have some CHiP-seq intervals from two
transcription factors I think might be involved in regulating the
genes that have changed. I have overlapping the CHiP-seq intervals
with two different definitions of what the regulatory region of a gene
might be - the promotor, defined as 2kb up- and down-stream of the TSS
and regulatory regions as defined by the GREAT tool. From each of
these overlaps I have pulled out the names of the overlapping
genes. My database contains 5 tables::

    differential
    Promoters_with_erg
    Promoters_with_ar
    greatdomains_with_erg
    greatdomains_with_ar

The `differential` table contains the results of the differential
expression analysis. Here are the first 10 rows:

.. report:: Genelists.DifferentialHead
   :render: table

   First 10 rows of the differential table

Each of the other tables contains a list of genes for which there is
an overlap between a CHiP-seq interval for one of the two TFs and the
regulatory region of that gene


.. report:: Genelists.GeneListHead
   :render: table

   First 10 rows of Promoters_with_ar

I want to know what the overlap of my up and down regulated genes is
for each of the two factors, for each of the two definitions of the
regulatory region.


Defining a tracker
-------------------


The first thing we must do is define the tracker that will return our
results. First import the tracker::

    from CGATReport.Tracker import *

Now we must define the tracker that will return our results. There are
lots of comparisons here and we must decide what are tracks and slices
are here. I've decided that the `tracks` will be the different
definitions of the regulatory region, and the `slices` will seperate
the Up and down regulated genes. The `tracks` can be sepcified using a
pattern on the database (the different tracks appear in the names of
the tables). The `slices` will have to be specified manually::

    from CGATReport.Tracker import *
    class OverlapTracker( TrackerOverlappingLists ):
        pattern = "(.+)_with_.+"
        slices=["logFC < 0", "logFC > 0"]

This tracker will now have two tracks and two slices:
* tracks: Promoters, greatdomains
* slices: logFC < 0, logFC > 0

Now I need to specify the the SQL statements. For each track/slice
combination I want to look at the overlap between three lists of
genes:

1. The genes differentially regulated
2. The genes bound by AR
3. The genes bound by ERG

The easiest way to do this is to specify the `ListA`, `ListB` and
`ListC` attributes to the tracker::

    from CGATReport.Tracker import *
    class OverlapTracker( TrackerMultipleLists ):
        pattern = "(.+)_with_.+"
        slices=["logFC < 0", "logFC > 0"]
       	
	ListA = '''SELECT gene_id
                   FROM differential
                   WHERE FDR < 0.05 AND %(slice)s '''

	ListB = '''SELECT gene_id
	           FROM %(track)s_with_ar '''

	ListC = '''SELECT gene_id
                   FROM %(track)s_with_erg'''

	labels = ["Differentially Expressed",
	          "Bound by AR",
                  "Bound by ERG" ]


Note how I've used the ``%(track)`` and ``%(slice)`` place holders in
the SQL statements, these will be substuted when the querys are
executed. Now because hypergeometric testing requires a background, we
need to produce a background list. For example, the differential
testing used here didn't test genes that arn't expressed in either
sample, so there is no way they could be in the differential set. So
our background set is all genes that appear in the differential
table::
    
    from CGATReport.Tracker import *
    class OverlapTracker( TrackerMultipleLists ):
        pattern = "(.+)_with_.+"
        slices=["logFC < 0", "logFC > 0"]
       	
	ListA = '''SELECT id
                   FROM differential
                   WHERE FDR < 0.05 AND %(slice)s '''

	ListB = '''SELECT gene_id
	           FROM %(track)s_with_ar '''

	ListC = '''SELECT gene_id
                   FROM %(track)s_with_erg'''

	background = '''SELECT id FROM differential'''

	#we also need to add backround to the labels
	labels = ["Differentially Expressed",
	          "Bound by AR",
                  "Bound by ERG",
		  "background" ]

Now we are almost finised. There is only one problem. Our background
is all genes in the differential table. But there could be genes in
the Bound genes lists that arn't in the background, so we need to
limit these::

    from CGATReport.Tracker import *
    class OverlapTracker( TrackerMultipleLists ):
        pattern = "(.+)_with_.+"
        slices=["logFC < 0", "logFC > 0"]
       	
	ListA = '''SELECT id
                   FROM differential
                   WHERE FDR < 0.05 AND %(slice)s '''

	ListB = '''SELECT gene_id
	           FROM %(track)s_with_ar as ar,
                        differential as diff
                   WHERE ar.gene_id = diff.id'''

	ListC = '''SELECT gene_id
                   FROM %(track)s_with_erg as erg,
                         differential as diff
                   WHERE erg.gene_id = diff.id'''

	background = '''SELECT id FROM differential'''

	#we also need to add backround to the labels
	labels = ["Differentially Expressed",
	          "Bound by AR",
                  "Bound by ERG",
		  "background" ]

Now we have finished our tracker. Lets see if it works using the table 
:term:`Renderer`:

.. report:: Genelists.OverlapTracker
   :render: debug

   Output from the OverlapTracker


Don't worry if you don't understand this. What we are seeing is a
nested dictionary. There are two entries on the top level "logFC < 0"
and "logFC > 0", then each of those has entries "greatdomains" and
"Promoters". At the bottom level each entry contains four lists of
gene ids.

Plotting venns
---------------

Now we've got our gene lists, lets have a look at the overlaps. One
way to visualise this is as a venn diagram. We already have a
`venn-plot` render, but it requires the data to be as a dictionary
with entries like '01','10' and '11', which specify the number of
items in the first set but not the second, the second set but not the
first and in both sets respectively, while our data is as lists of
genes. This is where the venn transformer comes in. It takes our gene
lists and computes the entries for the dictionary that venn-plot
takes. It will work on 2 and 3 way intersections. Lets see this on our
Tracker:

.. report:: Genelists.OverlapTracker
   :render: debug
   :transform: venn
   :slices: logFC < 0
   :tracks: Promoters
   

   Output from the debug render from our venn transformed tracker data
   for one slice and one track.

So we are now ready to plot these are venn diagrams, using a block
like this in our report::

    .. report:: Genelists.OverlapTracker
       :render: venn-plot
       :transform: venn
       :layout: grid

       add caption here

And the results look like this:


.. report:: Genelists.OverlapTracker
   :render: venn-plot
   :transform: venn
   :layout: grid

   Venn diagrams showing the overlap between Up and down regulated
   genes and CHiP-seq intervals

Note that the background list has been ignored for the sake of
plotting the venn diagrams. If you really want to keep it, add the
options ``:keep-background:`` but remeber that venn-plot can only do 3
way overlaps max.

Calculating Enrichments and p-values
-------------------------------------

Its all very well looking at overlapping venn diagrams, but we don't
know if the size of the overlaps is more or less than we would expect
by chance. This where the ``hypergeometric`` transformer comes in. It
looks at how big the overlap between the lists are compared to what
you would expect by chance and calculates a p-value based on the
hypergeometric distribution. Using it is as simple as transforming and
then rendering using a table:

.. report:: Genelists.OverlapTracker
   :render: table
   :transform: hypergeometric
   :tracks: Promoters
   :slices: logFC < 0

   Statitics on the overlap between Down regulated genes and genes
   with AR or ERG signals at their promoters.


Note that because there are three lists (plus the background) the
transformer calculates the stats for all pairwise
combinations. Awesome. But there are three tests here, and this only
one track and one slice. There are two tracks and two slices, each
with three tests. Thats a total 2x2x3=12 tests. We might worry that we
will run into a multiple testing problem. Not to worry. The
``p-adjust`` transformer will take any data that has a P-value column
(or other column sepecied using the ``:p-value:`` option) and correct
the p-values for multiple testing, adding these corrected values as a
new column:

.. report:: Genelists.OverlapTracker
   :render: table
   :transform: hypergeometric,p-adjust

   Statistics with adjusted P-values

By default ``p-adjust`` corrects accross the whole set of p-values,
but you can restrict it to just correct within a slice using
``:adj-levels: 2`` or just within one track/slice combination with
``:adj-levels: 1``. The default correction is a BH correction, but any
correction method understood by R's p.adjust function can be specified
using ``:adj-method:``.

Conclusion
----------

So there you have it. In 16 lines of Tracker code and 6 lines of rst
code we have calclated the overlap between two TFs and Up or Down
regulated genes for two different difinitions of the regulator region
of a gene, plotted them as venn diagrams and calculated the stats on
that. Clearly for simple comparisions with only two lists and no
tracks or slices, the process is even easier.


