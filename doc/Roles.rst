=====
Roles
=====

In addition to the ``:report:`` directive, sphinxreport provides some roles 
for inline text.

pmid
====

The ``:pmid:`` role links to the pubmed database via a pubmed id.
For example, use ``:pmid:`12706730`` to link to the pubmed entry
:pmid:`12706730`.

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





