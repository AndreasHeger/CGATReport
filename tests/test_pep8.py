import os
import pep8
from nose.tools import ok_


def check_pep8(filename):

    pep8style = pep8.StyleGuide(max_line_length=120)

    result = pep8style.check_files([filename])
    ok_(result.total_errors == 0,
        "Found code style errors (and warnings).")


def test_pep8():
    for root, dirs, files in os.walk('..'):
        for fn in files:
            if fn.endswith(".py"):
                yield(check_pep8,
                      os.path.abspath(os.path.join(
                          root, fn)))
