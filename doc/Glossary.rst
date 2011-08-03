d*********
Glossary
*********

.. glossary::
   :sorted:

   report
      The restructured text directive supplied by the SphinxSqlPlot extension.

   track
      A data set, for example species like "frog", "mouse", and "dog".

   slice
      A slice through a data set, for example gender like "male" and "female". 

   tracker
      A python function or functor returning data, see
      :class:`SphinxReport.Tracker.Tracker`.

   transformer
      A python class transforming data before rendering. 

   renderer
      An object displaying data returned from a :term:`Tracker`.

   path
      Data is stored hierarchically in a nested dictionary. The sequence of keys to 
      access a data item is called the path.

   functor
      A python object that can be used as a function. Functors define a ``__call__`` method. 

   labeled values
      ``label, value`` pairs in a nested dictionary. This
      data structure is understood by many renderers. An example of
      labeled data is::

            blue/car/wheels=4
      	    blue/car/doors=3
	    blue/bike/wheels=2
	    blue/bike/doors=0
	    red/car/wheels=4
	    red/car/doors=5

      Here, ``blue`` and ``red`` are :term:`track`, ``car`` and
      ``bike`` are :term:`slice` and ``weels=4`` is a ``label,value`` pair.

   numerical arrays
      numerical arrays are lists of numbers.

   labeled values with errors
      :term:`labeled values` can be extended with labels or errors.

            blue/car/wheels/data=4
            blue/car/wheels/data=4


      Here, ``blue`` and ``red`` are a :term:`track`, ``car`` and
      ``bike`` are a :term:`slice` and ``weels=4`` is a ``label,value`` pair.

   source directory
      The directory which, including its subdirectories, contains all source
      files for one Sphinx project.

   configuration directory
      The directory containing :file:`conf.py`.  By default, this is the same as
      the :term:`source directory`, but can be set differently with the **-c**
      command-line option.

   data tree
      nested dictionary used to represent labeled data

   data path
      path towards some data in a :term:`data tree`.
