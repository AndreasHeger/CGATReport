.. _Tutorial14:

===============================================
Plotting with the ipython notebook
===============================================

Introduction
============

In this tutorial we will be looking at the integration
of ipython_ and cgatreport_.

Let us say that we have computed meta-gene profiles for
a variety of datasets. The results are stored in a collection
of files in the :file:`data` directory::

    data/mC-foetal-dex-R2.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/mC-foetal-sal-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/hmC-foetal-dex-R2.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/hmC-foetal-sal-R2.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/hmC-input-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/mC-foetal-dex-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/hmC-foetal-sal-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/mC-foetal-sal-R2.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/mC-input-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz
    data/hmC-foetal-dex-R1.transcriptprofile.tsv.gz.geneprofile.matrix.tsv.gz

Each file is a table with multiple columns in a tab-separated format::

    bin     region  region_bin      none    area    counts  background
    0       upstream        0       37713.0 0.000295029382699       1.64937677673   0.966852493017
    1       upstream        1       37739.0 0.000295232781101       1.65051388585   0.96751905799
    2       upstream        2       37698.0 0.000294912037466       1.64872075224   0.966467936302
    3       upstream        3       37655.0 0.000294575647801       1.6468401487    0.965365540386
    4       upstream        4       37645.0 0.000294497417646       1.64640279904   0.965109169242
    5       upstream        5       37695.0 0.00029488856842        1.64858954734   0.966391024959
    6       upstream        6       37719.0 0.000295076320791       1.64963918653   0.967006315703
    7       upstream        7       37718.0 0.000295068497776       1.64959545156   0.966980678589
    8       upstream        8       37739.0 0.000295232781101       1.65051388585   0.96751905799

The columns are:

* ``bin``: x-coordinate of meta-gene profile
* ``region``: region within meta-gene profile (upstream,CDS,downstream)
* ``region_bin``: x-coordinate withit an region
* ``none``, ``area``, ``counts``, ``background``: various normalized metagene profiles

Moving to an ipython notebook
=============================

We are not certain which normalization method works best and so we want
to play around with the data before adding it to our report. We will use
an ipython_ session for this.

As the data is present in tabular format in a collection of files, we can use one of
the prepared cgatreport :term:`trackers` directly. First, we only want to get the
data for integration into our notebook. We type::

   cgatreport-test -r none -t TrackerDataframes -o glob='transcriptprofiles.dir/*.tsv.gz' -l notebook

This produces the following output::

   .. Template start

   %matplotlib inline
   import CGATReport.test
   result = CGATReport.test.main( do_print = False,
   tracker="TrackerDataframes",
   renderer="none",
   trackerdir="/ifs/devel/andreas/sphinx-report/doc/trackers",
   workdir="/ifs/devel/andreas/sphinx-report/doc",
   glob=transcriptprofiles.dir/*.tsv.gz )

   .. Template end
   --> cgatreport - available data structures <--
       result=<class 'collections.OrderedDict'>
       dataframe=<type 'NoneType'>

This statement will not render the data, but simply return a snippet for us to
include in our ipython note. Copy the text between ``.. Template start`` and
``.. Template end`` into your ipython notebook.

Please follow further instructions see this :download:`notebook
<CGATReportTutorial14.html>`.

Back to cgatreport
====================

Within the notebook, we have used ggplot for plotting. We now want to integrate
this plot into our report. To do this, we can again make use of :ref:`cgatreport-test` to 
create an rst snippet to copy and paste into our report::

    cgatreport-test -r ggplot -t TrackerDataframes -o glob="data/*.tsv.gz" -o aes='x="bin", y="background", color="track"' -o geom="geom_point()" -o regex="data/(.*).transcript*"

The output provides us with the snippet to put into the report::

    .. report:: Tracker.TrackerDataframes
       :render: ggplot
       :regex: data/(.*).transcript*
       :glob: data/*.tsv.gz
       :aes: x="bin", y="background", color="track"
       :geom: geom_point()
       :groupby: all

       Methylation profiles of transcripts

.. report:: Tracker.TrackerDataframes
   :render: ggplot
   :regex: data/(.*).transcript*
   :glob: data/*.tsv.gz
   :aes: x="bin", y="background", color="track"
   :geom: geom_point()
   :groupby: all

   Methylation profiles of transcripts

We can now use some of CGATReport's grouping capabilities in order to create plots 
that will be useful if many tracks are being plotted. The following will plot at most 5
data sets (``split-at``) and always include the ``input`` tracks (``split-always``) 
in each plot::

    .. report:: Tracker.TrackerDataframes
       :render: ggplot
       :regex: data/(.*).transcript*
       :glob: data/*.tsv.gz
       :aes: x="bin", y="background", color="track"
       :geom: geom_point()
       :split-at: 5
       :split-always: input
       :layout: row
       :groupby: all

       Methylation profiles of transcripts

.. report:: Tracker.TrackerDataframes
   :render: ggplot
   :regex: data/(.*).transcript*
   :glob: data/*.tsv.gz
   :aes: x="bin", y="background", color="track"
   :geom: geom_point()
   :split-at: 5
   :split-always: input
   :layout: row
   :groupby: all
	    
   Methylation profiles of transcripts

And back to the notebook again
==============================

The example has shown how cgatreport can be used as a data source
within an ipython notebook and how a ggplot in the ipython notebook can then
be reproduced within a report.

However, we can go beyond a complete circle. Note the ``nb`` link
below each figure in a CGATreport. By clicking on the link and
copying the displayed snipped into your notebook, you can get include
cgatreport generated plots and the resulting dataframe for
inspection. This is very useful for elaborationg on cgatreport
rendered plots in a notebook.









 





