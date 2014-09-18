.. _dataframe:

=========
dataframe
=========

:class:`CGATReportPlugins.Renderer.DataFrame` is useful for
debugging purposes and will most often be used with the
:ref:`cgatreport-test` utility.

.. report:: Trackers.LabeledDataExample
   :render: dataframe
   
   Dataframe built by CGATReport that is being sent
   to a Renderer.

Options
-------

:class:`CGATReportPlugins.Renderer.DataFrame` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   head
      integer
 
      Output a limited number of lines from the top of
      the dataframe. Can be combined with :term:`tail`.

   tail
      integer

      Output a limited number of lines from the bottom of
      the dataframe. Can be combined with :term:`head`.
      

   summary
      flag
 
      Instead of the data, output a per-column summary of the
      dataframe's contents.
