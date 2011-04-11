===============
Advanced topics
===============

This page collects a few advanced techniques for working with sphinxreport.

Referring to other sphinxreport documents
=========================================

The intersphinx_ extension permits referring to other
sphinxreport documents. To use this extension, add the following to
your :file:`conf.py` configuration file::

    extensions = [ ..., 'sphinx.ext.intersphinx', ...]

    intersphinx_mapping = {'<identifier>': ('<>', None) }

where identifier is a suitable identifier and ``absolute path name to html`` is 
the absolute location of the html build of the sphinx document you want
to refer to. This directory should contain the :file:`objects.inv` file. The
file is automatically created by sphinx, but sphinx needs to be run at least
once.

To refer to the other documentation, type::

   :ref:`My link to another documentation <identifier:label>`

Where ``label`` needs to be a valid identifier in the referred to document.

Using macros from another sphinxreport document
===============================================

Using macros from another sphinxreport document is possible if the
``linked-to`` sphinxreport document follows certain coding conventions. Basically,
the ``linked-to`` sphinxreport document needs to encapsulate all the configuration 
information that is specific to a project, in particular the location of data and database.
Here is an example of how it works.

Let's say we have a ``master`` document that wants to refer to the document created by an automated
generic rnaseq pipeline and a generic chipseq pipeline. 

The ``linked-to`` rnaseq document reads all its configuration from the ``rnaseq`` section in the :file:``sphinxreport.ini``::

   [rnaseq]
   exportdir=export
   datadir=.
   backend=sqlite:///./csvdb

Similarly, the ``linked-to`` chipseq document has a ``chipseq`` section in the :file:`sphinxreport.ini`::

   [chipseq]
   exportdir=export
   datadir=.
   backend=sqlite:///./csvdb

The ``master document`` contains both sections. Assuming that the two ``linked-to`` documents are siblings of
the master documents in the file hierarchy::

   [rnaseq]
   exportdir=../rnaseq/export
   datadir=../rnaseq
   backend=sqlite:///../rnaseq/csvdb

   [chipseq]
   exportdir=export
   datadir=.
   backend=sqlite:///./chipseq/csvdb

In order embed a macro from the ``linked-to`` rnaseq document, the ``master`` document 
will contain text like::

   .. report:: pipeline_docs.pipeline_rnaseq.trackers.Mapping.TophatSummary
      :render: table

      Number of alignments that align in a certain genomic context

Note how the `report` directive contains additional qualifiers for the location of the
rnaseq code. This is good practice to avoid namespace conflicts between trackers of the
same name in different documents.

The top of the hierarchy, ``pipeline_docs``, needs to be part of ``sys.path``, for example by
adding it to the :file:`conf.py` configuration file of the ``master`` documentation::

   sys.path.extend( ["/path/to/rnaseq/code", "/path/to/chipseq/code" ]

Implementation issues
---------------------

If you want that other sphinxreport documents can refer to your trackers, you need to make sure that
you encapsulate all configuration information into a single configuration section. Thus you should 
refrain from using and of the generic sections like ``[report]`` or ``[general]``. 

The best way to do this is to create a base tracker that all trackers within a project are derived from. 
In the example below, the trackers are all derived from the :class:`RnaseqTracker` class::

   EXPORTDIR=P['rnaseq_exportdir']
   DATADIR=P['rnaseq_datadir']
   DATABASE=P['rnaseq_backend']

   class RnaseqTracker( TrackerSQL ):
       '''Define convenience tracks for plots'''
       def __init__(self, *args, **kwargs ):
           TrackerSQL.__init__(self, *args, backend = DATABASE, **kwargs )

   class TophatSummary( RnaseqTracker, SingleTableTrackerRows ):
       table = "tophat_stats"

   class TranscriptCoverage(RnaseqTracker):
       """Coverage of reference transcripts."""
       pattern = "(.*)_transcript_counts$" 
       def __call__(self, track, slice = None ):
           data = self.getValues( """SELECT coverage_pcovered FROM %(track)s_transcript_counts""" )
           return odict( (("covered", data ) ,) )

The mixing of RnaseqTracker and :class:`SingleTableTrackerRows` illustrates how classes provided by sphinxreport
can be parameterized. Note that the order is important, RnaseqTracker needs to appear first to make sure that
its constructor is called first.

.. _intersphinx: http://sphinx.pocoo.org/latest/ext/intersphinx.html
