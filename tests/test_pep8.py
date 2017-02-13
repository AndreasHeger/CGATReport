import os
import pep8
from nose.tools import ok_
import CGATReport


def check_pep8(filename):

    # E731: do not assign a lambda expression, use a def

    pep8style = pep8.StyleGuide(max_line_length=120,
                                ignore="E731")

    result = pep8style.check_files([filename])
    ok_(result.total_errors == 0,
        "Found code style errors (and warnings).")


def test_pep8():

    for base in [CGATReport.__file__]:
        for root, dirs, files in os.walk(os.path.dirname(base)):
            for fn in files:
                if fn.endswith(".py") and not fn.startswith("."):
                    yield(check_pep8,
                          os.path.abspath(os.path.join(
                              root, fn)))
