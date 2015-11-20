============
Data mapping
============

This page describes how CGATReport assembles a :term:`dataframe` from
the data supplied by a :term:`tracker`. If you are uncertain, both can
be interactively queried with :term:`cgatreport-test` with the 
``-i/--interactive`` command line option. For example::

   cgatreport-test -t LabeledDataExample -i
   >>> ...
   >>> print dataframe
                  column1  column2  column3
   track  slice
   track1 slice1        1        2      NaN
          slice2        2        4        6
   track2 slice1        2        4      NaN
          slice2        4        8       12
   track3 slice1        3        6      NaN
          slice2        6       12       18

In the interactive python session, the variable ``dataframe`` contains
the :term:`dataframe` being built by CGATReport.

The output received from the :term:`tracker` is available in the
variable ``result``::

   >>> print result
   OrderedDict([('track1', OrderedDict([('slice1',
   OrderedDict([('column1', 1), ('column2', 2)])), ('slice2',
   OrderedDict([('column1', 2), ('column2', 4), ('column3', 6)]))])),
   ('track2', OrderedDict([('slice1', OrderedDict([('column1', 2),
   ('column2', 4)])), ('slice2', OrderedDict([('column1', 4),
   ('column2', 8), ('column3', 12)]))])), ('track3',
   OrderedDict([('slice1', OrderedDict([('column1', 3), ('column2',
   6)])), ('slice2', OrderedDict([('column1', 6), ('column2', 12),
   ('column3', 18)]))]))])

``result`` is a nested dictionary containing various data types. The
hierarchy in the dictionary is built through :term:`tracks` and
:term:`slices` but additional levels can be added by the user.
CGATReport only requires that the hierarchy is well-formed:
the depth of the hierarchy is uniform and the data types consistent.

The section below lists the datatypes that CGATReport accepts as
return types from a :term:`tracker`.

Scalars
=======

Scalar values such us numbers or text are the most basic type of data
a :term:`Tracker` can return.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnValue
    
.. report:: DataMapping.ReturnValue
   :render: dataframe
   :groupby: all

   Tracker returning a scalar

If the tracker returns slices, the slices will be added as columns:

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnValueWithSlice
    
.. report:: DataMapping.ReturnValueWithSlice
   :render: dataframe
   :groupby: all

   Tracker returning a scalar

If the :term:`tracker` adds additional levels is the dictionary,
they will be added as columns:

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnValueInDictionary

.. report:: DataMapping.ReturnValueInDictionary
   :render: dataframe
   :groupby: all

   Tracker returning a scalar in a dictionary

Arrays
======

Array-type data are python lists, python tuples or numpy_ arrays.

If all arrays at the leaves of the hierarchical dictionary
have the same size, they are assumed to be coordinate data, for example
x, y and z values. The resultant dataframe will have multiple columns:

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnArray
    
.. report:: DataMapping.ReturnArray
   :render: dataframe
   :groupby: all
   :head: 10
   :tail: 10

   Tracker returning an array

Note that coordinate data need not be actual coordinates, they could
equally be multiple observations on a sample. As all arrays have the
same size the implicit assumption is that the arrays are ordered.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnArrayWithSlice
    
.. report:: DataMapping.ReturnArrayWithSlice
   :render: dataframe
   :groupby: all
   :head: 10
   :tail: 10

   Tracker returning an array

If the arrays have different lengths, they are assumed to be a
collection of measurements, for example, height measurements in 
a treatment and a control group of individuals.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnVariableLengthArray
    
.. report:: DataMapping.ReturnVariableLengthArray
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Tracker returning an array

Sometimes arrays might have the same length but are not coordinate
data. In order to prevent these data from being treated as coordinate
data, the following workarounds are possible:

1. use the :ref:`melt` transformer
   (:class:`CGATReportPlugins.Transformer.TransformerMelt`)
2. return a DataFrame instead of a list of values, for example:

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnArrayWithSliceAsDataframe

.. report:: DataMapping.ReturnArrayWithSliceAsDataframe
   :render: dataframe
   :groupby: all
   :head: 10
   :tail: 10

   Tracker returning an array as dataframe and thus preventing it
   from being treated as coordinate data.

Dataframes
==========

A :term:`tracker` can return a pandas_ :term:`dataframe` directly.
Returning a :term:`dataframe` avoids any issues that might occur
through the data translation from the :term:`datatree` to the
:term:`dataframe`.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnDataFrameSimple
    
.. report:: DataMapping.ReturnDataFrameSimple
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Tracker returning a dataframe

In a :term:`dataframe` with column labels, the labels will be
preserved and the columns of the same name aligned.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnDataFrameWithColumnLabel
    
.. report:: DataMapping.ReturnDataFrameWithColumnLabel
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Tracker returning a dataframe

In a :term:`dataframe` with different labels, the labels will be
preserved and missing values added as ``NaN``.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnDataFrameWithColumnLabels
    
.. report:: DataMapping.ReturnDataFrameWithColumnLabels
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Tracker returning a dataframe

In a :term:`dataframe` with index, the index will be preserved as
part of a hierarchical index that will also include the :term:`tracks`
and :term:`slices`.

.. literalinclude:: trackers/DataMapping.py
   :pyobject: ReturnDataFrameWithIndex
    
.. report:: DataMapping.ReturnDataFrameWithIndex
   :render: dataframe
   :groupby: all
   :head: 5
   :tail: 5

   Tracker returning a dataframe

Special cases
=============

There are certain special cases. To be covered:

TODO:

* Status
* Venn
