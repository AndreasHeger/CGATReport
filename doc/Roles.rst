=====
Roles
=====

In addition to the ``:report:`` directive, cgatreport provides some roles 
for inline text.


pmid
====

The ``:pmid:`` role links to the pubmed database via a pubmed id.
For example, use ``:pmid:`12706730``` to link to the pubmed entry
:pmid:`12706730`.



biogps
======

The ``:biogps:`` role links to the `biogps <http://biogps.org>`_ site.
To use the role, supply an identifier understood by biogps, such as
a gene identifier, pathway identifier, etc.

For example, use ``:biogps:`ApoE``` to link to the gene information 
for :biogps:`ApoE`.


ucsc
====

The ``:ucsc:`` role links to the `UCSC <http://genome.ucsc.edu>`_ genome
browser. To use, supply a UCSC database identifier such as ``hg19``,
``mm10`` and valid coordinates. The identifier and coordinates should
be separated by the ``@`` character.

For example, use ``:ucsc:`hg19@chr8:132364392-132367460``` 
to link to the corresponding region on the human genome:
:ucsc:`hg19@chr8:132364392-132367460`.


ensembl
=======

The ``:ensembl:`` role links to the `ENSEMBL <http://ensembl.org>`_ genome
browser. To use, supply an ENSEMBL identifier such as ``BRCA2`` or
``ENSMUSG00000041147``.

For example, use ``:ensembl:`BRCA2``` to link to 
:ensembl:`BRCA2`.

If the text contains an ``@``, the text is assumed to contain an
ENSEMBL species identifier such as ``Mouse`` or ``Human`` to
limit the search.

For example, use ``:ensembl:`Mouse@ENSMUSG00000041147``` to link to 
:ensembl:`Mouse@ENSMUSG00000041147`.


param
=====

The ``:param:`` role displays field in classes. For example, use
``:param:`MyModule.MyClass.data``` to insert the content of
the member variable ``data`` from class ``MyClass`` in module
``MyModule``.

The following should work:
    
* :param:`TestCases.LargeMatrix.wordsize`.

The following should give errors during the build:

* :param:`wordsize` 
* :param:`TestCases.UnknownMatrix.wordsize` 
* :param:`TestCases.LargeMatrix.unknown_parameter` 

value
=====

The ``:value:`` role inserts a single value from a :term:`tracker` into
text. For example, use ``:param:`Module.myfunction``` to insert
the content of ``myfunction`` in module ``Module``.

For example, this is a result of value :value:`Trackers.getSingleValue`.





