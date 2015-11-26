=====================
Example Use Case
=====================

This section demonstrates the typical CGATReport workflow by building
a report from a relational database.

This is a typical use case. Usually you would have some automated
process or pipeline that generates data. CGATReport is then used
to produce a report from the data.

Background
==========

The database is from a short-read mapping experiment. You can download and
restore the example database from::

   wget http://www.cgat.org/~andreas/documentation/CGATReportExamples/data/usecase1/csvdb.dump.gz
   zcat csvdb.dump.gz | sqlite3 csvdb

The file :file:`csvdb` is an sqlite_ database. It contains summary
data created by the CGAT short read mapping pipeline.

There are two kinds of tables in the database. Track tables contain
data for a particular data-set. For example, the table
``UHR_F1_R1_bowtie_transcript_counts`` contains ``transcript count``
data for the track (or data set) ``UHR_F1_R1_bowtie``. The data set is
derived by mapping short reads in the UHR_F1_R1 data set using
bowtie_.

The various tables are

intron_counts
	reads overlapping introns
transcript_counts
	reads overlapping transcripts
overrun
	reads extending beyond exon boundaries

The second class of tables are summary tables which contain 
data about multiple tracks. For example, the table ``reads_summary``
is a table with the number of reads per input data set.

The tables are:

bam_stats
	summary statistics of :term:`bam` files
bam_stats_nh
	summary statistics of :term:`bam` files - number of hits
bam_stats_nm
	summary statistics of :term:`bam` files - number of mismatches
context_stats
	overlap statistics of reads with various genomic regions
exon_validation
	exon validation statistics
star_stats
	mapping summary from star_ mapper
tophat_stats
	mapping summary from tophat_ mapper
view_mapping
	a summary view of mapping information

Setting up the report
=====================

The aim of CGATReport is to make report writing easy. To get going,
type::

   cgatreport-quickstart -d report

This will create a skeleton report in the directory :file:`report`. The main page is
:file:`contents.rst` and it has two sections, :file:`pipeline.rst`
and :file:`analysis.rst`. 

Let us enter the :file:`report` directory and see if the report builds::

   cd report
   make html; firefox _build/html/contents.html

CGATReport lets you write your report as you perform the analysis.
Before we start, let us tell CGATReport where to find our database.
To do this, open the file :file:`cgatreport.ini` and change the line::

   sql_backend=sqlite:///./csvdb

to the location of where the previously downloaded database
:file:`csvdb` is located. If you followed the example above,
:file:`csvdb` is in the parent directory of the report, thus the
following should work::

   sql_backend=sqlite:///../csvdb

There are many options in :file:`cgatreport.ini` and :file:`conf.py`
that govern the look and feel of the report. They are very well worth
experimenting with, but in this example we will go straight to the analysis.

Recording the first observations
================================

Open the :file:`analysis/Results.rst` and add some introduction, such as::

     Once upon a midnight dreary, while I pondered weak and weary,
     Over many a quaint and curious volume of forgotten lore,
     While I nodded, nearly napping, suddenly I started mapping,
     Short-read data mapping, mapping fast and multi-core.
     `Must be a nutter,' I muttered, `mapping multi-core -
     Same story, nothing more.'

Let's see what happend during last night's mapping frenzy.
To begin, let us display a table with the number of reads input.
To do this, we need to define a data source. Open the 
:file:`trackers/Tracker.py` and add the following lines::

   class ReadsSummary(SingleTableTrackerRows):
      table = 'reads_summary'

This short statement creates a new :term:`Tracker`. It is derived
from the class
:class:`CGATReport.Tracker.SingleTableTrackerRows`. This tracker
collects data from a single table with multiple tracks. To check if
it works, type on the command line::

   cgatreport-test -r table -t ReadsSummary

Now you can simply copy and paste the template into the file
:file:`analysis/Results.rst`::
  
   Thus I mapped:	 

   .. report:: Trackers.ReadsSummary
     :render: table

     Summary table with reads to be mapped.

Numbers are good, but what about presenting the data as a bar-chart?
As this changes only the representation of the data while the data
itself remains unchanged, we can re-use the existing :term:`Tracker`.
Type on the command line::

   cgatreport-test -r interleaved-bar-plot -t ReadsSummary

:ref:`cgatreport-test` can be used to fine-tune the representation
of a plot. For example, let us get rid of the legend::

   cgatreport-test -r interleaved-bar-plot -t ReadsSummary -o legend-location=none

All options accessible in cgatreport can be passed to the :term:`Renderer`
with the ``-o/--option`` keyword argument.

Now paste the following into :file:`analysis/Results.rst`::

   Bleary eyed, I queried for readier display:

   .. report:: Trackers.ReadsSummary
     :render: interleaved-bar-plot
     :legend-location: none

     Summary of reads input

Now we want to make a notice of the minimum and maximum number of reads
input. We add the following two trackers::

    class MinReadsInput(TrackerSQL):
       def __call__(self):
	  return self.getValue('SELECT min(total_reads) FROM reads_summary') 

    class MaxReadsInput(TrackerSQL):
       def __call__(self):
	  return self.getValue('SELECT max(total_reads) FROM reads_summary') 

We can now add these to our report. Add the following to
:file:`analysis/Results.rst`::

   Good heavens, I exclaimed, I mapped between
   :value:`Trackers.MinReadsInput` and :value:`Trackers.MaxReadsInput` reads.

We can now re-build the report and examine the result::

   make html; firefox _build/html/contents.html

This short example illustrates the typical workflow when
writing a report with cgatreport:

   1. Write a :term:`Tracker` to collect the data.
   2. Test the data source with :ref:`cgatreport-test`.
   3. Refine the representation with :ref:`cgatreport-test`.
   4. Interprete the data with different representations/trackers.
   5. Write thoughts into restructured text document and add
      macro to display data supporting the text.

What seems like a lot of effort to create a table, bar-chart and an
observation will pay off once a report gets larger. The report as it
is can be updated if the underlying data has changed with a single
command. The report can also be re-used on a different data just by
simply pointing to a different database.

Working with data frames
========================

The underlying data structure in CGATReport is the pandas_
dataframe. There are multiple ways to create, interact and visualize
the dataframe directly.

To easily create a dataframe, the :mod:`.Tracker` module provides
classes to derive your own :term:`trackers` from. For example,
:class:`.TrackerDataframes` builds dataframes from multiple
tab-separated files on disk. :class:`.TrackerSQL` has a method
:meth:`.getDataFrame` to return a dataframe from the result of an SQL
query.

The :term:`renderer` :ref:`dataframe` displays a dataframe and can
be used by :term:`cgatreport-test` to see the data structure.

The :term:`transformer` :ref:`pandas` applies any pandas dataframe
transformations such as melt, pivot, stack, etc.

The :term:`renderer` :ref:`pdplot` produces plots implemented in
pandas.

Notes
=====

In order to work effectively, the following setup works quite well:

1. An editor (such as emacs) with multiple buffers open (rst-file,
   python-file with trackers, ...) - usually side-by-side in 
   a split window.
2. A command line shell for testing with :ref:`cgatreport-test`
   and exploring the database via SQL commands.
3. A web browser (firefox) with multiple tabs pointed at the
   various parts of the report that are in progress.


Tracks and slices
=================

Now that we now where we started, let us add some results. In this
section we introduce :term:`tracks` and :term:`slices` more
thoroughly.

:term:`tracks` and :term:`slices` are cgatreport terminology. An
alternative labeling would be as ``track=dataset`` and
``slice=measurement``. For example, :term:`tracks` or data sets could
be ``mouse``, ``human``, ``rabbit`` and :term:`slices` or measurements
could be ``height`` and ``weight``. This nomenclature explains why
default grouping in plots is by :term:`slice` - the above
:term:`tracks` and :term:`slices` would be displayed as two plots for
``height`` and ``weight`` contrasting the various heights and weights
for the three species.


The aligned reads are stored in :term:`bam` formatted files and the
table ``bam_stats`` contains some summary statistics on these
:term:`bam` files.

To start with, we will add another :term:`Tracker`. As with the table
``reads_summary``, the table ``bam_stats`` is a multi-track
table. Thus, the following tracker is sufficient to give us access to
all the data::

   class BamStats(SingleTableTrackerRows):
      '''bam file summary statistics.'''
      table = 'bam_stats'

This :term:`tracker` defines each row as a :term:`track`. There should
be column called ``track`` in the table, but others columns can be
specified. Each field in a row is a different :term:`slice`.

Again, you can test the tracker on the command line::

   cgatreport-test -r table -t BamStats

Wait, no table? The output you will see is::

    `60 x 27 table <#$html $#>`__

By default, cgatreport puts large tables into a separate file and
links to it. In order to see it on the command line or force entering
it into the main page, add the ``force`` option::

   cgatreport-test -r table -t BamStats -o force

Now we get the table, but we feel it is too large to enter into the
report. Let us enter just the slices we are interested in, such as the
reads in the :term:`bam` file and the number of mapped reads::

   cgatreport-test -r table -t BamStats -o force -o slices=reads_total,reads_mapped

Again, we would prefer displaying the data as a bar plot::

   cgatreport-test -r interleaved-bar-plot -t BamStats -o force -o slices=reads_total,reads_mapped

Copy the template into :file:`analysis/Results.rst`, maybe with some
text::

   Ere I mapped:

   .. report:: Trackers.BamStats
      :render: interleaved-bar-plot
      :slices: reads_total,reads_mapped   

      Number of total and mapped reads in bam file
     
We still find the plot to busy and we want to add our conclusions.
Let us draw attention to certain features of the data, for example by
selecting only tracks of interest::

   Too much I mapped, my mouth ajar

   Quoth the star:

   .. report:: Trackers.BamStats
      :render: interleaved-bar-plot
      :slices: reads_total,reads_mapped
      :tracks: r(star)

      Number of total and mapped reads in bam file from the star mapper.
 
Note how we selected both the :term:`slices` and the :term:`tracks` to
display - the letter using a regular expression syntax.

We now want to examine what percentage of reads mapped. Unfortunately,
this is beyond :class:`SingleTableTrackerRows` and we need to write
our own tracker::

    class BamStatsPercentMappedReads(TrackerSQL):

       def getTracks( self ):
          return self.getValues("SELECT DISTINCT track FROM bam_stats")

       def __call__(self, track ):
          return self.getValue(
	      "SELECT 100.0 * reads_mapped/reads_total "
   	      FROM bam_stats WHERE track = '%(track)s'")

As before, try out the tracker on the command line and fine-tune the
representation with :ref:`cgatreport-test`. Once happy, enter into the
report::

    Quoth the star (in percent):

    .. report:: Trackers.BamStatsPercentMappedReads
       :render: interleaved-bar-plot
       :tracks: r(star)

       Percentage of mapped reads from the star mapper.

Using transformers
===================

So far we have only looked at single tables that contained multiple
tracks. Now we will look at more complex processing where the data is
arranged in multiple tables and needs to be processed in order to
generate a plot.

Let us say we are interested to plot the distribution of coverag
transcripts have achieved by short-read data. The data has
conveniently been computed in our analysis pipeline and is in the
tables ``<track>_transcript_counts``. The columns we are interested in
are the columns ``coverage_sense_pcovered``,
``coverage_antisense_pcovered`` and ``coverage_anysense_pcovered`` for
percent coverage by reads in sense, antisense or any direction.

The :term:`tracker` is now derived from :class:`TrackerSQL`. Add the
following to :file:`Trackers.py`::

    class TranscriptCoverage(TrackerSQL):
       '''transcript coverage.'''

       pattern = '(.*)_transcript_counts$'

       slices = ('coverage_anysense_pcovered',
                 'coverage_antisense_pcovered',
                 'coverage_sense_pcovered')

       def __call__(self,track,slice):
	  return self.getValues(
	      "SELECT %(slice)s FROM %(track)s_transcript_counts")

TrackerSQL provides a connection to the database together whether
some convenience functions. The attribute :term:`pattern` allows you to define
a set of tables as :term:`tracks` - the group in the regular expression gives
the :term:`track` names. The attribute :term:`slices` defines the
slices.

Note how the __call__ method makes use of automatic string
substitution. ``%(slice)s`` and ``%(track)s`` will be replaced by the
contents of the variable names ``track`` and ``slice``.

Now that we have the data, we can test the tracker. A good way to do
this is by using the :class:`Debug` renderer. Type on the command
line::

   cgatreport-test -r debug -t TranscriptCoverage

The tracker works and we can display it using a boxplot. Add the
following to :file:`analysis/Results.rst`::

    Then this fast mapper beguiling my sad fancy into smiling,
    By the grave and stern decorum of the the countenance it wore,
    'Mappest thou plenty and with speed', I said 'art thou my savior?
    Ghastly grim and ancient mapper from my nightly chore
    Tell me what thy mapping rigor is on the transcript coverage score,
    Quoth the star (as boxplots):

    .. report:: Trackers.TranscriptCoverage
       :render: box-plot

       Box plot of transcript coverage.

Let us say we wanted to display the densities. To do this we need to
transform the data points into a histogram. This conversion could be
encoded into a separate tracker, but in order to permit re-use of
trackers as much as possible, cgatreport allows you to add
transformations to data before it is rendered. The transformer we need
here is :class:`TransformerHistogram`. Again, the :class:`Debug`
renderer can show us what is happening::

   cgatreport-test -r debug -t TranscriptCoverage -m histogram

Note how each measurement is transformed from a simple list of values
to a dictionary of two items, a list of bins and a list of values. 
Add the following to :file:`analysis/Results.rst`::

    Quoth the star (as densities):

    .. report:: Trackers.TranscriptCoverage
       :render: line-plot
       :as-lines:
       :tracks: r(star)
       :transform: histogram

       Transcript coverage

At this stage, my report looks like this:

http://www.cgat.org/~andreas/documentation/CGATReportExamples/usecase1/_build/html/analysis/Results.html

Conclusions
===========

In this worked example we have introduced how cgatreport can be used
to perform interactive and reproducible analysis.

Further on
==========

Using this use case, try to implement the following analyses:

1. Insert density plots of intron coverage (table introns) similar to
   the one for transcript coverage.

   .. note:: 
      Think about code-reuse

2. Insert a plot with the correlation of transcript coverage and
   intron coverage.
   
   .. note::
      Think about table joins in SQL. For example, the following will
      report the maximum coverage per gene::

            SELECT MAX(i.coverage_anysense_max),
	           MAX(t.coverage_anysense_max) 
	    FROM uhr_f1_r1_bwa_transcript_counts AS t, 
	         uhr_f1_r1_bwa_intron_counts AS i, 
		 refcoding_transcript2gene AS m
	    WHERE m.gene_id = i.gene_id AND 
	          m.transcript_id = t.transcript_id
	    GROUP BY i.gene_id" 
 
      Note the use of the table ``refcoding_transcript2gene`` to
      translate transcript identifiers to gene identifiers.

3. Insert a table with correlation coefficients of transcript and
   intron coverage

   .. note::
      Think about Transformers

4. Insert a table with the number of transcripts with 80% transcript
   coverage.
   
   .. note::
      Think about counting in SQL. Make the threshold a variable 
      and enter a refence into the text using the ``:param:`` role.

5. Insert a square table with the number of transcripts that have 80%
   transcript coverage for each pair of tracks, such as:

   +--------+------------+--------------+
   |        | Track1     | Track2       |
   +--------+------------+--------------+
   | Track1 | 5000       | 3000         |
   +--------+------------+--------------+
   | Track2 | 3000       | 5000         |
   +--------+------------+--------------+

   .. note::
      Think about table joins in SQL.

6. Insert a matrix plot from the previous table.

   .. note::
      Think about ordering the table.

.. glossary::

   bam
      a genomic file format


.. _bowtie: http://bowtie-bio.sourceforge.net/index.shtml
.. _tophat: http://tophat.cbcb.umd.edu/index.shtml
.. _star: http://code.google.com/p/rna-star/



