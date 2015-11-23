.. _Tutorial6:

=============================
Customizing plots
=============================

Plots are customized by options supplied to the ``:report:``
directive. Different renderers permit different options. For a full
list, see the :ref:`Reference`.

Building from the example of :ref:`Tutorial5` we will now

   * make a single plot using the ``groupby`` option,
   * plot only lines using the ``as-lines`` option, and
   * add an x-axis label using the ``xtitle`` option.

First, check the plot's look on the command line::

   cgatreport-test -t ExpressionLevelWithSlices -r line-plot -m histogram -o range=0,100,4 -o groupby=all -o as-lines -o xtitle="expression level"

If you are satisfied, add the following text to your document:

.. literalinclude:: Tutorial6Demo.rst
   :lines: 19-28

Note that the same data can often be presented in different ways. For
example, you might be interested in the stats of these functions:

.. literalinclude:: Tutorial6Demo.rst
   :lines: 32-37

display a box plot:

.. literalinclude:: Tutorial6Demo.rst
   :lines: 41-47
 
or might want to present the histogram literally:

.. literalinclude:: Tutorial6Demo.rst
   :lines: 51-58		   

See :ref:`Tutorial6Demo` to check how the result should look like.
