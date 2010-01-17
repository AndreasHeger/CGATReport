Testing the roles
=================

PMID
====

The ``:pmid:`` role links to the pubmed database via a pubmed id.

For example, see :pmid:`12706730` on protein domains.

Parameter
=========

The ``:param:`` role displays field in classes. For example, to get
the parameter mWordSize: :param:`TestCases.LargeMatrix.mWordSize` .

The following should give errors during the build:

   * :param:`mWordSize` 
   * :param:`TestCases.UnknownMatrix.mWordSize` 
   * :param:`TestCases.LargeMatrix.unknown_parameter` 

