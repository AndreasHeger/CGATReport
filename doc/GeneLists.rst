======================
Working with Genelists
======================

Examining the overlaps between gene lists is something we do
frequently. To make this easier CGATReport contains a set of tools
to make it easier. 

Overview 
========

The tools you need to work with gene lists are a tracker and three renders.

* :class:`CGATReport.Tracker.TrackerMultipleLists`: This tracker takes a set of SQL queries and
  returns a dictionary of lists, where each list is of items, such as
  gene names.

There are two transformers that take the lists and examine the overlap
between the lists.

* :ref:`venn`: The venn transformer takes a dictionary of lists and
  transforms the data so that it is in the correct format for plotting
  a venn diagram of the overlaps between the lists.

* :ref:`hypergeometric`: The hypergeometric transformer takes a dictionary of
  lists and calculates the enrichements and p-values for the overlaps
  using the hypergeometric distribution. If there are more than two
  lists, all pairwise combinations will be computed.

* :ref:`p-adjust`: A utility function that looks for a P-value column in a
  table and computes multiple testing corrected p-values and adds
  these as a new column in the table.

The idea is that the user will define a subclass of
TrackerMultipleLists, then either transform the data using
:ref:`venn` for plotting with :ref:`venn-plot` or use 
:ref:`hypergeometric` to calculate statistics to display as a table
or plot such as a :ref:`bar-plot`.

The TrackerMultipleLists tracker
====================================

The transformers should work out of the box and transparently
without much interference from the user, but the tracker is a
little more complex, so we will have a look at how it works.
	
What TrackerMultipleLists does is take a set of SQL lists
and produces a dictionary of lists, where each list is the
result of each query. So for example you might have two SQL
statements were each statement returns a list of gene ids that
where the genes returned from two experiments.

These SQL statements can be defined in three ways:

1. The first method is to subclass the tracker set the `ListA` and `ListB`
attributes to the two different SQL statements. You can do this for
attributes called `ListA`, `ListB`, `ListC` and `background`. Because
`ListA`, `ListB` etc, isn’t very descriptive, you can give these lists
names by setting the labels attribute of your Tracker. e.g.::

    class MyListsTracker( TrackerMultipleLists ): ListA="SELECT
        gene_id FROM experiment_one_genes" ListB="SELECT gene_id FROM
        experiment_two_genes" labels = ["Experiment One","Experiment
        Two"]
         
2. The easiest way is to set an attribute called
statements. Statements should be a dictionary of SQL statements. In
this case the names are taken from the dictionary keys. e.g.::

    class MyListsTracker( TrackerMultipleLists ): statements =
        {"Experiment One": "SELECT gene_id FROM experiment_one_genes",
        "Experiment Two": "SELECT gene_id FROM experiment_two_genes"}

3. Finally, if you want more flexibility you can overwrite the
:meth:`CGATReport.Tracker.TrackerMultipleLists.getStatements`
method. In this you can do whatever you like as long as
you return a dictionary of SQL statements.

Because `TrackerMultipleLists` is a `TrackerSQL` tracker, slices
and trackers are specified as you would expect, and you can use them
in your SQL statements queries.

Finally, because in order to perform hypergeometric tests you need a
background set, if you intend to perform hypergeometric testing, one
of the lists your Tracker returns should be called ``background``. If you
transform to venn format using the :ref:`venn` transformer, this list will
be automatically removed (unless you explicitly tell the transformer
not to this with the `keep-background` option).

