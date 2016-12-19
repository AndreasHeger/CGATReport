=================
Unicode rendering
=================

Unicode rendering of text in python 2.7 is disabled, unicode
characters are replaced by ``?``:

.. report:: Unicode.LabeledDataExampleUnicode
   :render: table
   
   A table with Unicode tracks and slices. In python 2.7,
   unicode characters in report text are masked.

However, unicode text in restructured text documents is fine, for
example beta is β.
