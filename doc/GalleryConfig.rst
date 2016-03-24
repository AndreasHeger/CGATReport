.. _config:

======
config
======

The :class:`CGATReport.Tracker.Config` reads configuration values 
from a cgatreport`ConfigParser` formatted file. These can then be displayed
using the :ref:`table` renderer.

.. report:: Tracker.Config
   :tracks: conf.ini
   :render: table
   
   Table with pipeline parameters.

Config values are available in the report to turn on/off particular
sections.

.. ifconfig:: config_variable_int == 1

   Now you see me...

.. ifconfig:: config_variable_int == 2

   now you don't.



