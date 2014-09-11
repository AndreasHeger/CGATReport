
class DataSimple(object):

    """Base class for data types.

    Derived classes enforce consistency checks on data.
    """
    __slots__ = ["_instance", "_data", "_fn"]

    def __init__(self, fn):
        """Store data returned by function."""
        object.__setattr__(self, "_fn", fn)
        object.__setattr__(self, "_data", None)
        object.__setattr__(self, "_instance", None)

    def __call__(self, *args, **kwargs):
        """call the function and return a clone of one-self.
        """
        # Decorators will use the same object for each decoration
        # and data will get overwritten in successive calls to the same function.
        # Thus clone oneself before storing the data and return
        # the clone.
        clone = copy.copy(self)
        setattr(clone, "_data", self._fn(self._instance, *args, **kwargs))
        clone.__check__()
        return clone

    def __len__(self):
        return len(self._data)

    def __get__(self, instance, cls=None):
        object.__setattr__(self, "_instance", instance)
        return self

    def __getstate__(self):
        # previously used deepcoy, but not necessary
        return {"_data": self._data}

    def __setstate__(self, dict):
        for key, val in dict.items():
            object.__setattr__(self, key, val)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, *args, **kwargs):
        return self._data.__getitem__(*args, **kwargs)

    def __setslice__(self, *args, **kwargs):
        return self._data.__getslice__(*args, **kwargs)

    def __contains__(self):
        return self._data.__contains__(*args, **kwargs)

    def __copy__(self):
        return self.__class__(self)
#    def __getattr__(self, name):
#        return getattr(self._data, name)
#    def __setattr__(self, name, value):
#        setattr(self._data, name, value)


class Data(object):

    """Base class for data types.

    Derived classes enforce consistency checks on data.
    """
    __slots__ = ["_data"]

    def __init__(self, data):
        """Store data returned by function."""
        object.__setattr__(self, "_data", data)
        if data:
            self.__check__()

    def __len__(self):
        return len(self._data)

    def __getstate__(self):
        # previously used deepcoy, but not necessary
        return {"_data": self._data}

    def __setstate__(self, dict):
        for key, val in dict.items():
            object.__setattr__(self, key, val)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, *args, **kwargs):
        return self._data.__getitem__(*args, **kwargs)

    def __setslice__(self, *args, **kwargs):
        return self._data.__getslice__(*args, **kwargs)

    def __contains__(self):
        return self._data.__contains__(*args, **kwargs)

    def __copy__(self):
        return self.__class__(self)
#    def __getattr__(self, name):
#        return getattr(self._data, name)
#    def __setattr__(self, name, value):
#        setattr(self._data, name, value)


class SingleColumn(Data):

    """Single column.

    The data can be any scalar type.

    Example: (1,2,"a")
    """

    def __init__(self, fn):
        Data.__init__(self, fn)

    def __check__(self):
        assert type(self._data) in ContainerTypes, "returned type is not a collection: %s" % (
            type(self._data))
        for x in self._data:
            assert type(x) in NumberTypes, "value %s is not a number: type=%s" % (
                str(x), type(x))


class SingleColumnData(Data):

    """Single column data.

    All data are numerical values.

    Example: (1,2,3)
    """

    def __init__(self, fn):
        Data.__init__(self, fn)

    def __check__(self):
        assert type(self._data) in ContainerTypes, "returned type is not a collection: %s" % (
            type(self._data))
        for x in self._data:
            assert type(x) in NumberTypes, "value %s is not a number: type=%s" % (
                str(x), type(x))


class MultipleColumns(Data):

    """Multiple column data

    The data can be any scalar type. All columns have the same length.

    Example: (("column1", "column2"), (("val1",2,3), ("val2",2,3)))
    """

    def __init__(self, fn):
        Data.__init__(self, fn)

    def __check__(self):
        assert type(self._data) in ContainerTypes, "returned type is not a collection: %s" % (
            type(self._data))
        assert type(self._data[0]) in ContainerTypes, "first column is not a collection: %s" % (
            type(self._data[0]))
        assert type(self._data[1]) in ContainerTypes, "second column is not a collection: %s" % (
            type(self._data[1]))
        for c in self._data[1]:
            assert type(
                c) in ContainerTypes, "column is not a collection: %s" % (type(c))
        try:
            assert min([len(c) for c in self._data[1]]) == max([len(c) for c in self._data[1]]), \
                "data columns have not the same length: %i != %i." %\
                (min([len(c) for c in self._data[1]]), max([len(c)
                                                            for c in self._data[1]]))
        except ValueError as msg:
            # ignore errors due to empty sequences
            pass


class MultipleColumnData(Data):

    """Multiple column data

    All data are numerical values.

    Example: (("column1", "column2"), ((1,2,3), (1,2,3)))
    """

    def __init__(self, fn):
        Data.__init__(self, fn)

    def __check__(self):
        assert type(self._data) in ContainerTypes, "returned type is not a collection: %s" % (
            type(self._data))
        assert type(self._data[0]) in ContainerTypes, "first field is not a collection: %s" % (
            type(self._data[0]))
        assert type(self._data[1]) in ContainerTypes, "second field is not a collection: %s" % (
            type(self._data[1]))
        for c in self._data[1]:
            assert type(
                c) in ContainerTypes, "column is not a collection: %s" % (type(c))
            for x in c:
                assert type(x) in NumberTypes, "value %s is not a number: type=%s" % (
                    str(x), type(x))
        assert min([len(c) for c in self._data[1]]) == max(
            [len(c) for c in self._data[1]]), "data columns have not the same length."


class LabeledData(Data):

    """Labeled data points.

    Data can be of any type.  There is only one value per label.

    Example: (("column1", 1), ("column2",2))
    """

    def __init__(self, fn):
        Data.__init__(self, fn)

    def __check__(self):
        assert type(
            self._data) in ContainerTypes, "returned type is not a collection: %s" % (self._data)
        for x in self._data:
            assert type(
                x) in ContainerTypes, "row is not a collection: %s" % str(x)
            assert len(
                x) == 2, "data is not a column, value tuple: %s" % str(x)


def returnLabeledValue(Data):
    """decorator for Trackers returning:class:`LabeledValue`."""
    def wrapped_f(*args, **kwargs):
        return LabeledValue(f(*args, **kwargs))
    return wrapped_f


def returnSingleColumn(f):
    """decorator for Trackers returning:class:`SingleColumn`."""
    def wrapped_f(*args, **kwargs):
        return SingleColumn(f(*args, **kwargs))
    return wrapped_f


def returnSingleColumnData(f):
    """decorator for Trackers returning:class:`SingleColumnData`."""
    def wrapped_f(*args, **kwargs):
        return SingleColumnData(f(*args, **kwargs))
    return wrapped_f


def returnMultipleColumns(f):
    """decorator for Trackers returning:class:`MultipleColumn`."""
    def wrapped_f(*args, **kwargs):
        return MultipleColumns(f(*args, **kwargs))
    return wrapped_f


def returnMultipleColumnData(f):
    """decorator for Trackers returning:class:`MultipleColumnData`."""
    def wrapped_f(*args, **kwargs):
        return MultipleColumnData(f(*args, **kwargs))
    return wrapped_f


def returnLabeledData(f):
    """decorator for Trackers returning:class:`LabeledData`."""
    def wrapped_f(*args, **kwargs):
        return LabeledData(f(*args, **kwargs))
    return wrapped_f

# def returnSingleColumn(f):
#     """decorator for Trackers returning:class:`SingleColumn`."""
#     return SingleColumn(f)

# def returnSingleColumnData(f):
#     """decorator for Trackers returning:class:`SingleColumnData`."""
#     return SingleColumnData(f)

# def returnMultipleColumns(f):
#     """decorator for Trackers returning:class:`MultipleColumn`."""
#     return MultipleColumns(f)

# def returnMultipleColumnData(f):
#     """decorator for Trackers returning:class:`MultipleColumnData`."""
#     return MultipleColumnData(f)

# def returnLabeledData(f):
#     """decorator for Trackers returning:class:`LabeledData`."""
#     return LabeledData(f)
