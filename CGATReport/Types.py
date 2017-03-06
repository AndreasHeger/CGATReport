import numpy
import pandas
import re
from collections import OrderedDict
from six import string_types, integer_types

ContainerTypes = (tuple, list, type(numpy.zeros(0)))
DictionaryTypes = (dict, OrderedDict)

# Taken from numpy.ScalarType, but removing the types object and unicode
# None is allowed to represent missing values. numpy.float128 is a recent
# numpy addition.
try:
    FloatTypes = (float,
                  numpy.float32, numpy.float64, numpy.float128)
    IntTypes = integer_types + (
        numpy.int8, numpy.int16,
        numpy.int32, numpy.int64,
        numpy.uint8, numpy.uint16,
        numpy.uint32, numpy.uint64)

except AttributeError as msg:
    FloatTypes = (float,
                  numpy.float32, numpy.float64)
    IntTypes = integer_types + (
        numpy.int8, numpy.int16,
        numpy.int32, numpy.int64,
        numpy.uint8, numpy.uint16,
        numpy.uint32, numpy.uint64)

NumberTypes = IntTypes + FloatTypes + (type(None),)


def is_dataframe(data):
    '''return True if data is a dataframe.'''
    return type(data) == pandas.DataFrame


def is_dataseries(data):
    '''return True if data is a series.'''
    return type(data) == pandas.Series


def is_array(data):
    '''return True if data is an array.'''
    return type(data) in ContainerTypes


def is_matrix(data):
    '''return True if data is a numpy matrix.

    A matrix is an array with two dimensions.
    '''
    return isinstance(data, numpy.ndarray) and len(data.shape) == 2


def is_dict(data):
    '''return True if data is a dictionary'''
    return type(data) in DictionaryTypes


def is_int(obj):
    return type(obj) in IntTypes


def is_float(obj):
    return type(obj) in FloatTypes


def is_string(obj):
    # Python 3
    # return isinstance(obj, str)
    return isinstance(obj, string_types)


def is_numeric(obj):
    attrs = ['__add__', '__sub__', '__mul__', '__div__', '__pow__']
    return all(hasattr(obj, attr) for attr in attrs)


def as_list(param):
    '''return a param as a list'''
    if type(param) not in (list, tuple):
        p = param.strip()
        if p:
            return [x.strip() for x in p.split(",")]
        else:
            return []
    else:
        return param


def to_string(value, format="%i"):
    '''returns a number as string

    If not a number, return empty string.'''

    try:
        return format % value
    except TypeError:
        return ""
    except ValueError:
        return "nan"


def quote_rst(text):
    '''quote text for restructured text.'''
    return re.sub(r"([*])", r"\\\1", str(text))


def quote_filename(text):
    '''quote filename for use as link in restructured text (remove spaces,
    quotes, slashes, etc).

    latex does not permit a "." for image files.

    Note that the quoting removes slashes and backslashes and thus removes
    any path information.

    Replace all with "_"

    '''
    return re.sub(r"""[ '"()\[\]./]""", r"_", str(text))


def get_encoding():
    # TODO: hard-coded for now, parameterize later.
    return "utf-8"


def force_decode(s, encoding="utf-8", errors="replace"):
    if s is None:
        return None
    return s.decode(encoding, errors=errors)


def force_encode(s, encoding="utf-8", errors="replace"):
    if s is None:
        return None
    return s.encode(encoding, errors=errors)


def force_dataframe_encode(df, encoding="utf-8", errors="replace"):
    df = df.reset_index()
    columns = [x for x, y in zip(df.columns, df.dtypes) if y == object]
    for col in columns:
        try:
            df[col] = df[col].str.decode("unicode-escape").str.encode(
                encoding, errors=errors)
        except AttributeError:
            # non-string columns
            pass
    return df
