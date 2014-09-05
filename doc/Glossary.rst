*********
Glossary
*********

.. glossary::
   :sorted:

   report
      The restructured text directive supplied by CGAReport.

   dataframe
      A dictionary like data structure for tabular data.
      Dataframes have been implemented in pandas_

   hierarchical index
      Rows (and columns) can be indexed in a pandas_
      :term:`dataframe`. This indexing can be done on
      multiple levels. CGATReport uses a hierachical
      index on rows to separate data sets. The first
      two levels are called :term:`track` and :term:`slice`.

   track
   tracks
      A data set, for example species like "frog", "mouse", and "dog".

   slice
   slices
      A measurement of a data set, for example 'height', 'weight', but also
      a slice of subset of data, for example gender like "male" and
      "female" 

   tracker
   trackers
      A python function or functor returning data, see
      :class:`CGATReport.Tracker.Tracker`.

   transformer
   transformers
      A python class transforming data before rendering. 

   renderer
   renderers
      An object displaying data returned from a :term:`Tracker`.

   path
      Data is stored hierarchically in a nested dictionary. The sequence of keys to 
      access a data item is called the path.

   functor 
      A python object that can be used as a function. Functors
      define a ``__call__`` method.  labeled values ``label, value``
      pairs in a nested dictionary. This data structure is understood
      by many renderers. An example of labeled data is::

            blue/car/wheels=4
      	    blue/car/doors=3
	    blue/bike/wheels=2
	    blue/bike/doors=0
	    red/car/wheels=4
	    red/car/doors=5

      Here, ``blue`` and ``red`` are :term:`track`, ``car`` and
      ``bike`` are :term:`slice` and ``weels=4`` is a ``label,value`` pair.

   numerical arrays
      numerical arrays are lists of numbers, for example::

         blue/car/tankfillings=(40,40,45,30,20)
         blue/car/pumpprices=(60,62,40,32,21)
         red/car/tankfillings=(30,30,35,30,20)
         red/car/pumpprices=(30,32,30,32,21)

   matrix
   matrices
      matrices are represented as a dictionary with the three mandatory
      entries: ``matrix``, ``rows``, ``columns``. The matrix field
      contains a numpy_ matrix, ``rows`` is a list of row names and 
      ``columns`` is a list of column names.  For example::

         matrix=[[1,2,3],[2,4,2]]
	 rows=["row1", "row2"]
	 columns=["column1", "column2", "column3"]
   
   data frame
   data frames
       is a generic data container used in R. 

   labeled values
      Labeled values are the most basic type of data in the data tree.
      Values are atomic and can be numbers or strings.

            car/wheels/4
            car/colour/blue
	    bike/wheels/4
	    bike/color/red

   labeled values with errors
      :term:`labeled values` can be extended with errors or labels
      using the words ``error`` and ``label``, respectively.

            blue/car/wheels/data=4
            blue/car/wheels/error=1
            blue/car/wheels/label=mycar
            red/bike/wheels/data=4
            red/bike/wheels/error=0
            red/bike/wheels/label=mybike

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

