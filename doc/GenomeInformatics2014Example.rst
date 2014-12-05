.. _GenomeInformatics2014Example:

.. This example was presented at GenomeInformatics 2014 as a poster.

=================
MeDIP-seq results
=================

We computed meta-gene profiles of MeDIP-seq and hMeDIP-seq data using
the :file:`pipeline_windows` pipeline. The results are stored in the
:file:`data` directory::

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

The background normalized meta-gene profiles are below:

.. report:: Tracker.TrackerDataframes
   :render: ggplot
   :regex: data/(.*).transcript*
   :glob: data/*.tsv.gz
   :aes: x="bin", y="background", color="track"
   :geom: geom_point()
   :groupby: all

   Background normalized metagene profiles

There is a smaller signal in the hMeDIP-seq compared to the MeDIP data.

The associated notebook is :download:`here <GenomeInformatics2014.html>`.
