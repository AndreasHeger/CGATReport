import os
import sys
import re
import warnings
import inspect
import logging
import glob
import gzip

from collections import OrderedDict as odict
import collections

# Python 2/3 Compatibility
try:
    import configparser as configparser
except:
    import configparser

import numpy
import pandas
import sqlalchemy
import sqlalchemy.exc as exc
import sqlalchemy.engine

from CGATReport import Utils
from CGATReport import Stats


class SQLError(Exception):
    pass


def prettyFloat(val, format="%5.2f"):
    """output a float or "na" if not defined"""
    try:
        x = format % val
    except (ValueError, TypeError):
        x = "na"
    return x


def prettyPercent(numerator, denominator, format="%5.2f"):
    """output a percent value or "na" if not defined"""
    try:
        x = format % (100.0 * numerator / denominator)
    except (ValueError, ZeroDivisionError):
        x = "na"
    return x


def getCallerLocals(level=3, decorators=0):
    '''returns locals of caller using frame.

    optional pass number of decorators

    from http://pylab.blogspot.com/2009/02/python-accessing-caller-locals-from.html
    '''
    f = sys._getframe(level + decorators)
    args = inspect.getargvalues(f)
    return args[3]


def quoteField(s):
    '''returns a quoted version of s for inclusion in SQL statements.'''
    # replace internal "'" with "\'"
    return re.sub("'", "''", s)


@Utils.memoized
def getTableNames(db, database=None, attach=None):
    '''return a set of table names.'''

    # attached databases do not show up in sqlalchemy, thus provide
    # a hack (for sqlite3 only)
    def _get(name):
        try:
            r = db.execute(
                "SELECT tbl_name FROM %s.sqlite_master" % name)
        except exc.SQLAlchemyError as msg:
            raise SQLError(msg)

        return ['%s.%s' % (name, x[0]) for x in r.fetchall()]

    if database is not None:
        return set(_get(database))

    result = []
    # get attached databases
    if attach:
        for path, name in attach:
            result.extend(_get(name))

    inspector = sqlalchemy.engine.reflection.Inspector.from_engine(db)
    result.extend(inspector.get_table_names())
    return set(result)


def getTableColumns(db, tablename, attach=None):
    '''return column information for table *tablename*.

    The returned information contains one dictionary per
    column. The column name is in the "name" field.
    
    If attach is not None, assume that engine is sqlite and
    use a direct query for table names.
    '''
    # for sqlite attached tables
    if attach and "." in tablename:
        # PRAGMA table_info(tablename) does not work as 
        # a "." in a table name will cause an error.
        # Thus select from sqlite_master in attached
        # database directly and parse the result.
        try:
            database, name = tablename.split(".")
            r = db.execute(
                """SELECT sql FROM %s.sqlite_master
                WHERE tbl_name = '%s' AND type = 'table'""" %
                (database, name))
        except exc.SQLAlchemyError as msg:
            raise SQLError(msg)
        # extract string from brackes onwards, ignore CREATE .... (
        s = r.fetchone()[0]
        s = s[s.index("(")+1:]
        # convert to dict for compatibility with sqlalchemy inspector
        vals = [{"name": x} for x in re.findall("(\S+)[^,]+,", s)]
    else:
        inspector = sqlalchemy.engine.reflection.Inspector.from_engine(db)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            vals = inspector.get_columns(tablename)

    return vals


class Tracker(object):
    """
    Base class for trackers. User trackers should be derived from this class.

    A tracker provides the data for a given:term:`track` through
    its __call__ method. Optionally, the data can be sliced, with
    a:term:`slice` containing a subset of the data.

    For example, tracks could be
    entities like cars, motorcycles, and bikes, and slices could
    be colours like blue, red, green::

       class LengthTracker(Tracker):
          mData = ...
          def __call__(self, track, slice):
             return [x.length for x in mData
                      if x.type == track and x.color == slice]

    The call::

       tracker = LengthTracker()
       tracker("car", "blue")

    would return the lengths of blue cars.

    This class accepts the following user arguments:

    datadir : string (optional)
       root directory in which data for this report is located.

    """

    mMinData = 1

    # set to False, if results of tracker should be cached
    cache = True

    # default: empty tracks/slices
    # tracks = []
    # slices = []
    # paths = []

    def __init__(self, *args, **kwargs):

        # directory where data for report is located
        if "datadir" in kwargs:
            self.datadir = kwargs["datadir"]
        elif "report_datadir" in Utils.PARAMS:
            self.datadir = Utils.PARAMS["report_datadir"]
        else:
            self.datadir = "."

        self.datadir = os.path.abspath(self.datadir)

    # def getTracks(self):
    #     """return a list of all tracks that this tracker provides."""
    #     return self.tracks

    # def getSlices(self):
    #     """return a list of all slices that this tracker provides.
    #     """
    #     return self.slices

    # def getPaths(self):
    #     """return all paths this tracker provides.
    #     """
    #     return self.paths

    def getShortCaption(self):
        """return one line caption.

        The default is to return the first non-blank line of the
        __doc__ string.

        """
        try:
            for line in self.__doc__.split("\n"):
                if line.strip():
                    return line.strip()
        except AttributeError:
            return ""
        return ""

    def __call__(self, track, slice=None):
        """return a data structure for track:param: track and slice:slice:"""
        raise NotImplementedError(
            "Tracker not fully implemented -> __call__ missing")

    def members(self, locals=None):
        '''function similar to locals() but returning member variables of this
        tracker.

        Convenience function for string substitution. If *locals* is
        given (and a dictionary), the dictionary is added to the
        returned dictionary. Entries in *local* take precedence before
        member variables.

        Typical usage is::

           print "my string with %(vars)s" % (self.members(locals())).

        returns a dictionary

        '''
        # skip tracks and slices to avoid recursion
        # todo: do this for the general case
        # 1. subtract property attributes, or
        # 2. subtract members of Tracker()
        l = dict([(attr, getattr(self, attr)) for attr in dir(self)
                  if not isinstance(attr, collections.Callable) and
                  not attr.startswith("__") and attr != "tracks"
                  and attr != "slices"])

        if locals:
            return dict(l, **locals)
        else:
            return l


class TrackerSingleFile(Tracker):

    '''base class for tracker obtaining data from a single file.

    Tracks and slices are defined by the file contents.
    '''

    def __init__(self, *args, **kwargs):
        Tracker.__init__(self, *args, **kwargs)
        if "filename" not in kwargs:
            raise ValueError(
                "TrackerSingleFile requires a:filename: parameter")

        self.filename = kwargs['filename'].strip()


class TrackerMultipleFiles(Tracker):

    '''base class for trackers obtaining data from a multiple files.

    Tracks are names derived from filenames via a
    regular expression.

    This tracker accepts the following parameters:

    :glob:

        glob expression describing the files to include.

    :regex:

        regular expression for extracting a track label from
        a filename. If not given, the complete filename
        path is used.

    '''
    # do not cache as retrieved directly from file
    # and is usually parameterized
    cache = False

    def getTracks(self, subset=None):

        self.mapTrack2File = {}
        for f in glob.glob(self.glob):
            try:
                track = self.regex.search(f).groups()[0]
            except AttributeError:
                raise ValueError(
                    "filename %s does not match regular expression" % f)

            self.mapTrack2File[track] = f
        return sorted(self.mapTrack2File.keys())

    def __init__(self, *args, **kwargs):
        Tracker.__init__(self, *args, **kwargs)
        if "glob" not in kwargs:
            raise ValueError("TrackerMultipleFiles requires a:glob: parameter")

        self.glob = kwargs['glob'].strip()
        self.regex = kwargs.get('regex', '(.*)')

        if '(' not in self.regex:
            raise ValueError(
                "regular expression requires exactly one group enclosed in ()")
        self.regex = re.compile(self.regex)

    def openFile(self, track):
        '''open a file.'''
        filename = self.mapTrack2File[track]
        if filename.endswith(".gz"):
            infile = gzip.open(filename, "r")
        else:
            infile = open(filename, "r")
        return infile


class TrackerTSV(TrackerSingleFile):

    """Base class for trackers that fetch data from an CSV file.

    Each track is a column in the file.
    """

    def __init__(self, *args, **kwargs):
        TrackerSingleFile.__init__(self, *args, **kwargs)

        self._data = None
        self._tracks = None

    def getTracks(self, subset=None):
        if self.filename.endswith(".gz"):
            inf = gzip.open(self.filename, "r")
        else:
            inf = open(self.filename, "r")

        for line in inf:
            if line.startswith("#"):
                continue
            tracks = line[:-1].split("\t")
            break
        inf.close()
        self._tracks = tracks
        return tracks

    def readData(self):
        if self._data is None:
            if self.filename.endswith(".gz"):
                inf = gzip.open(self.filename, "r")
            else:
                inf = open(self.filename, "r")

            data = [x.split()
                    for x in inf.readlines() if not x.startswith("#")]
            inf.close()

            self.data = dict(list(zip(data[0], list(zip(*data[1:])))))

    def __call__(self, track, **kwargs):
        """return a data structure for track:param: track"""
        self.readData()
        return self.data[track]


class TrackerMatrices(TrackerMultipleFiles):
    """Return matrix data from multiple files.
    """

    def __call__(self, track, **kwargs):
        """return a data structure for track:param: track"""

        infile = self.openFile(track)

        dtype = numpy.float

        lines = [l for l in infile.readlines() if not l.startswith("#")]
        infile.close()
        nrows = len(lines) - 1
        col_headers = lines[0][:-1].split("\t")[1:]
        ncols = len(col_headers)
        matrix = numpy.zeros((nrows, ncols), dtype=dtype)
        row_headers = []

        for row, l in enumerate(lines[1:]):
            data = l.split("\t")
            row_headers.append(data[0])
            matrix[row] = numpy.array(data[1:],
                                      dtype=dtype)

        # convert to floats/ints - in dataframe construction
        # columns get sorted lexicographical order if they
        # are strings.
        def _convert(l):
            try:
                return list(map(int, l))
            except ValueError:
                pass
            try:
                return list(map(float, l))
            except ValueError:
                pass
            return l

        row_headers = _convert(row_headers)
        col_headers = _convert(col_headers)

        return odict((('matrix', matrix),
                      ('rows', row_headers),
                      ('columns', col_headers)))


class TrackerDataframes(TrackerMultipleFiles):
    '''return dataframe from files.

    By default, the dataframe has no row names.
    If self.index_column is set, the specified column
    will be used as row names.
    '''

    def __init__(self, *args, **kwargs):
        TrackerMultipleFiles.__init__(self, *args, **kwargs)
        self.index_column = kwargs.get('index_column', None)

    def __call__(self, track, **kwargs):

        df = pandas.read_csv(self.openFile(track),
                             sep='\t',
                             header=0,
                             index_col=self.index_column)
        return df


class TrackerImages(Tracker):

    '''Collect image files and arrange them in a gallery.
    '''
    # do not cache as retrieved directly from file
    # and is usually parameterized
    cache = False

    def __init__(self, *args, **kwargs):
        Tracker.__init__(self, *args, **kwargs)
        if "glob" not in kwargs:
            raise ValueError("TrackerImages requires a:glob: parameter")
        self.glob = kwargs["glob"]

    def getTracks(self, subset=None):
        return glob.glob(self.glob)

    def __call__(self, track, **kwargs):
        """return a data structure for track:param: track and slice:slice:"""
        return {'filename': track}


class TrackerSQL(Tracker):
    """Base class for trackers that fetch data from an SQL database.

    The basic tracker identifies tracks as tables that match a
    certain pattern (:attr:`pattern`)

    The pattern should contain at least one group. If there are multiple
    groups, these will be associated as tracks/slices.

    This tracker connects to the database. Each tracker will establish
    its own connection for efficient multi-processing.

    If:attr:`as_tables` is set, the full table names will be returned.
    The default is to apply:attr:`pattern` and return the result.

    This class accepts the following user arguments:

    sql_backend : string (optional)
       SQL backend to use. The default is ``sqlite:///./csvdb``.

    """

    pattern = None
    as_tables = False

    def __init__(self, backend=None, attach=[], *args, **kwargs):
        Tracker.__init__(self, *args, **kwargs)

        # connection within python
        self.db = None

        # connection within R
        self.rdb = None

        # attach to additional tables
        self.attach = attach

        # set backend
        if backend is not None:
            # backend given to constructor
            self.backend = backend
        elif "sql_backend" in kwargs:
            # backend given by user parameter in report directive
            self.backend = kwargs["sql_backend"]
        elif not hasattr(self, "backend"):
            # not defined previously (by mix-in class) get default
            self.backend = Utils.PARAMS["report_sql_backend"]

        # patch for mPattern and mAsTables for backwards-compatibility
        if hasattr(self, "mPattern"):
            warnings.warn(
                "mPattern is deprecated, use pattern instead",
                DeprecationWarning)
            self.pattern = "(.*)%s" % self.mPattern
        if hasattr(self, "mAsTables"):
            warnings.warn(
                "mAsTables is deprecated, use as_tables instead",
                DeprecationWarning)
            self.as_tables = self.mAsTables

    def connect(self, creator=None):
        """lazy connection function."""

        if not self.db:

            logging.debug("connecting to %s" % self.backend)

            # attach to additional databases (sqlite)
            if self.attach:

                if creator is not None:
                    raise NotImplementedError(
                        'attach not implemented if creator is set')

                if not self.backend.startswith('sqlite'):
                    raise NotImplementedError(
                        'attach only implemented for sqlite backend')

                def _my_creator():
                    # issuing the ATTACH DATABASE into the sqlalchemy
                    # ORM (self.db.execute(...))
                    # does not work. The database is attached, but tables
                    # are not accessible in later
                    # SELECT statements.
                    import sqlite3
                    conn = sqlite3.connect(
                        re.sub("sqlite:///", "", self.backend))
                    for filename, name in self.attach:
                        conn.execute("ATTACH DATABASE '%s' AS %s" %
                                     (os.path.abspath(filename),
                                      name))
                    return conn
                creator = _my_creator

            # creator can not be None.
            if creator:
                db = sqlalchemy.create_engine(self.backend,
                                              echo=False,
                                              creator=creator)
            else:
                db = sqlalchemy.create_engine(self.backend,
                                              echo=False)

            if not db:
                raise ValueError(
                    "could not connect to database %s" % self.backend)

            db.echo = False

            # ignore unknown type BigInt warnings
            # Note that this step can take a while on large databases
            # with many tables and many columns
            if db and False:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.metadata = sqlalchemy.MetaData(
                            db, reflect=True)
                except AttributeError:
                    self.metadata = sqlalchemy.MetaData(db, reflect=True)

            self.db = db

            logging.debug("connected to %s" % self.backend)

    def rconnect(self, creator=None):
        '''open connection within R to database.'''

        if not self.rdb:

            R.library('RSQLite')

            if creator:
                self.rdb = creator()

            else:
                if self.backend.startswith('sqlite'):
                    self.rdb = R.dbConnect(
                        R.SQLite(), dbname=re.sub("sqlite:///./", "",
                                                  self.backend))
                else:
                    raise NotImplementedError(
                        "can not connect to %s in R" % self.backend)

    def getTables(self, pattern=None, database=None):
        """return a list of tables matching a *pattern*.

        This function does not return table views.

        If *database* is given, tables are returned from
        *database*.

        returns a sorted list of table names.
        """
        self.connect()
        sorted_tables = sorted(getTableNames(
            self.db,
            database=database,
            attach=self.attach))

        if pattern:
            rx = re.compile(pattern)
            return [x for x in sorted_tables if rx.search(x)]
        else:
            return sorted_tables

    def getTableNames(self, pattern=None):
        '''return a list of tablenames matching a *pattern*.
        '''
        return self.getTables(pattern)

    def hasTable(self, tablename):
        """return table with name *tablename*."""
        self.connect()
        return tablename in getTableNames(self.db, attach=self.attach)

    def getColumns(self, tablename):
        '''return a list of columns in table *tablename*.'''

        self.connect()
        columns = getTableColumns(self.db, tablename, attach=self.attach)

        return [re.sub("%s[.]" % tablename, "", x['name']) for x in columns]

    def getTracks(self, *args, **kwargs):
        """return a list of all tracks that this tracker provides.

        Tracks are defined as tables matching the attribute
        :attr:`pattern`.
        """
        if self.pattern:
            rx = re.compile(self.pattern)
            tables = self.getTables(pattern=self.pattern)
            if self.as_tables:
                return sorted([x for x in tables])
            else:
                return sorted([rx.search(x).groups()[0] for x in tables])
        else:
            return ["all"]

    def getPaths(self):
        """return all paths this tracker provides.

        Tracks are defined as tables matching the attribute
        :attr:`pattern`.

        """
        if self.pattern:
            rx = re.compile(self.pattern)
            # let getTracks handle a single group
            if rx.groups < 2:
                return None
            tables = self.getTables(pattern=self.pattern)
            parts = [rx.search(x).groups() for x in tables]
            result = []
            for x in range(rx.groups):
                result.append(sorted(set([part[x] for part in parts])))
            return result
        return None

    def execute(self, stmt):
        self.connect()
        try:
            r = self.db.execute(stmt)
        except exc.SQLAlchemyError as msg:
            raise SQLError(msg)
        return r

    def buildStatement(self, stmt):
        '''fill in placeholders in stmt.'''

        kwargs = self.members(getCallerLocals())
        statement = stmt % dict(list(kwargs.items()))
        return statement

    # --------------------------------------------------
    # Functions returning the results of SQL statements
    # as various python structures (dicts, lists, ...)

    def getFirstRow(self, stmt):
        """return a row of values from SQL statement *stmt* as a list.

        The SQL statement is subjected to variable interpolation.

        This function will return the first row from a SELECT statement
        as a list.

        Returns None if result is empty.
        """
        e = self.execute(self.buildStatement(stmt)).fetchone()
        if e:
            return list(e)
        else:
            return None

    def getRow(self, stmt):
        """return a row of values from an SQL statement as dictionary.

        This function will return the first row from a SELECT
        statement as a dictionary of column-value mappings.

        Returns None if result is empty.
        """
        e = self.execute(self.buildStatement(stmt)).fetchone()
        # assumes that values are sorted in ResultProxy.keys()
        if e:
            return odict([x, e[x]] for x in list(e.keys()))
        else:
            return None

    def getValues(self, stmt):
        """return values from SQL statement *stmt* as a list.

        This function will return the first value in each row
        from an SELECT statement.

        Returns an empty list if there is no result.
        """
        e = self.execute(self.buildStatement(stmt)).fetchall()

        if e:
            return [x[0] for x in e]
        return []

    def getAll(self, stmt):
        """return all rows from SQL statement *stmt* as a dictionary.

        This method is deprecated.

        The dictionary contains key/values pairs where keys are
        the selected columns and the values are the results.

        Example: SELECT column1, column2 FROM table
        Example: { 'column1': [1,2,3], 'column2': [2,4,2] }

        Returns an empty dictionary if there is no result.
        """
        # convert to tuples
        e = self.execute(self.buildStatement(stmt))
        columns = list(e.keys())
        d = e.fetchall()
        return odict(list(zip(columns, list(zip(*d)))))

    def get(self, stmt):
        """return all results from an SQL statement as list of tuples.

        Example: SELECT column1, column2 FROM table
        Result: [(1,2),(2,4),(3,2)]

        Returns an empty list if there is no result.
        """
        return self.execute(self.buildStatement(stmt)).fetchall()

    def getDict(self, stmt):
        """return results from SQL statement *stmt* as a dictionary.

        Example: SELECT column1, column2 FROM table
        Result: { 1: 2, 2: 4, 3: 2}

        The first column is taken as the dictionary key.

        This method is useful to return a data structure
        that can be used for matrix visualization.
        """
        # convert to tuples
        e = self.execute(self.buildStatement(stmt))
        columns = list(e.keys())
        result = odict()
        for row in e:
            result[row[0]] = odict(list(zip(columns[1:], row[1:])))
        return result

    # -------------------------------------
    # Convenience functions for access
    def getValue(self, stmt):
        """returns a single value from SQL statement *stmt*.

        If the result is empty, None is returned.

        The SQL statement is subjected to variable interpolation.

        This function will return the first value in the first row
        from a SELECT statement.
        """
        statement = self.buildStatement(stmt)
        result = self.execute(statement).fetchone()
        if result is None:
            return result
        return result[0]

    def getIter(self, stmt):
        '''returns an iterator over results of SQL statement *stmt*.
        '''
        return self.execute(stmt)

    def getDataFrame(self, stmt, **kwargs):
        '''return results of SQL statement as a pandas dataframe.

        kwargs are passed unchanged to the pandas.read_sql method.

        '''
        self.connect()
        return pandas.read_sql(self.buildStatement(stmt),
                               self.db,
                               **kwargs)

    # # -------------------------------------
    # # Direct access functios for return to CGATReport
    # def getRows(self, stmt):
    #     """return all results from an SQL statement as list of tuples.

    #     Example: SELECT column1, column2 FROM table
    #     Result: [(1,2),(2,4),(3,2)]

    #     Returns an empty list if there is no result.
    #     """
    #     return self.execute(self.buildStatement(stmt)).fetchall()

    # def get(self, stmt):
    #     """deprecated - use getRows instead."""
    #     return self.getRows(self.buildStatement(stmt))

    # def getAll(self, stmt):
    #     '''return results of SQL statement as pandas dataframe.
    #     '''
    #     return self.getDataFrame(self.buildStatement(stmt))

    # def getValues(self, stmt):
    #     '''return results of SQL statement as pandas Series.
    #     '''
    #     e = self.exectute(self.buildStatement(stmt))
    #     return pandas.Series([x[0] for x in e])

    # def getRow(self, stmt):
    #     '''return results of SQL statement as pandas dataframe
    #     '''
    #     e = self.execute(self.buildStatement(stmt))
    #     return pandas.Series(e.fetchone())

    # def getFirstRow(self, stmt):
    #     '''return first row of SQL statement as pandas Series.
    #     '''
    #     e = self.execute(self.buildStatement(stmt))
    #     return pandas.Series(e.fetchone())


class TrackerSQLCheckTables(TrackerSQL):
    """Tracker that examines the presence/absence of a certain
    field in a list of tables.

    Define the following attributes:

:attr:`pattern`: pattern to define tracks (see:class:`TrackerSql`)
:attr:`slices` columns to look for in tables

    """

    slices = None
    pattern = None
    as_tables = True

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def __call__(self, track, slice=None):
        """count number of unique occurances of field *slice* in tables
        matching *track*."""

        if slice not in self.getColumns(track):
            return None

        return self.getValue(
            "SELECT COUNT(DISTINCT %(slice)s) FROM %(track)s")


class TrackerSQLCheckTable(TrackerSQL):

    """Tracker that counts existing entries in a table.

    Define the following attributes:
:attr:`exclude_pattern`: columns to exclude
:attr:`pattern`: pattern to define tracks (see:class:`TrackerSql`)
    """

    exclude_pattern = None
    pattern = "(.*)_evol$"

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def __call__(self, track, *args):
        """count number of entries in a table."""

        statement = "SELECT COUNT(%s) FROM %s WHERE %s IS NOT NULL"

        if self.exclude_pattern:
            fskip = lambda x: re.search(self.exclude_pattern, x)
        else:
            fskip = lambda x: False

        tablename = track + "_evol"
        columns = self.getColumns(tablename)
        data = []

        for column in columns:
            if fskip(column):
                continue
            data.append(
                (column, self.getValue(statement % (column,
                                                    tablename,
                                                    column))))
        return odict(data)


class Config(Tracker):

    '''Tracker providing config values of ini files.

    The .ini files need to be located in the directory
    from which cgatreport is called.

    returns a dictionary of key,value pairs.
    '''
    tracks = glob.glob("*.ini")

    def __init__(self, *args, **kwargs):
        Tracker.__init__(self, *args, **kwargs)

    def __call__(self, track, *args):
        """count number of entries in a table."""

        config = configparser.ConfigParser()
        config.readfp(open(track), "r")

        result = odict()

        def convert(value):
            '''convert a value to int, float or str.'''
            rx_int = re.compile("^\s*[+-]*[0-9]+\s*$")
            rx_float = re.compile("^\s*[+-]*[0-9.]+[.+\-eE][+-]*[0-9.]*\s*$")

            if value is None:
                return value

            if rx_int.match(value):
                return int(value), "int"
            elif rx_float.match(value):
                return float(value), "float"
            return value, "string"

        for section in config.sections():
            x = odict()
            for key, value in config.items(section):
                x[key] = odict(list(zip(("value", "type"), convert(value))))
            result[section] = x

        return result


class Empty(Tracker):
    '''Empty tracker

    This tracker servers as placeholder for plots that require no
    input from a tracker.

    '''

    def getTracks(self, subset=None):
        """return a list of all tracks that this tracker provides."""
        return ["empty"]

    def __call__(self, *args):
        return None


class Status(TrackerSQL):

    '''Tracker returning status information.

    Define tracks and slices. Slices will be translated into
    calls to member functions starting with 'test'.

    Each test function should return a tuple with the test
    status and some information.

    If this tracker is paired with a:class:`Renderer.Status`
    renderer, the following values of a test status will be
    translated into icons: ``PASS``, ``FAIL``, ``WARNING``, ``NOT AVAILABLE``.

    The docstring of the test function is used as description.
    '''

    def getSlices(self, subset=None):
        return [x[4:] for x in dir(self) if x.startswith("test")]

    def __call__(self, track, slice):
        if not hasattr(self, "test%s" % slice):
            raise NotImplementedError("test%s not implement" % slice)

        status, value = getattr(self, "test%s" % slice)(track)
        description = getattr(self, "test%s" % slice).__doc__
        if description is None:
            description = ""

        return odict(
            (('name', slice),
             ('status', status),
             ('info', str(value)),
             ('description', description)))


class SQLStatementTracker(TrackerSQL):
    '''Tracker representing the result from an SQL statement.
    '''
    statement = None

    # columns to use as tracks
    fields = ("track",)

    def setIndex(self, dataframe):
        '''sets the index according to the fields given.'''
        # removes the "all" index and others
        dataframe.reset_index(drop=True, inplace=True)
        # set index
        try:
            dataframe.set_index(list(self.fields), inplace=True)
        except KeyError as msg:
            raise KeyError(
                "%s: have %s" %
                (msg, dataframe.columns))

    def __call__(self):
        if self.statement is None:
            raise NotImplementedError(
                "statement needs to be set for SQLStatementTracker")
        return self.getAll(self.statement)


class SingleTableTrackerRows(TrackerSQL):

    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of values.

    The tracks are given by rows in table :py:attr:`table`. The tracks are
    specified by the:py:attr:`fields`.

    :py:attr:`fields` is a tuple of column names (default = ``(track,)``).

    If multiple columns are specified, they will all be used to define
    the tracks in the table.

    Rows in the table need to be unique for any
    combination:py:attr:`fields`.

    :py:attr:`extra_columns` can be used to add additional columns to
    the table. This attribute is a dictionary, though only the keys
    are being used.

    :py:attr:`where` is an optional where that will be added as a
    WHERE clause to the SQL statement

    '''
    exclude_columns = ()
    table = None
    fields = ("track",)
    extra_columns = {}
    sort = None
    loaded = False
    where = None

    # not called by default as Mixin class
    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def _load(self):
        '''load data.

        The data is pre-loaded in order to avoid multiple random access
        operations on the same table.
        '''
        if not self.loaded:
            nfields = len(self.fields)

            if self.sort:
                sort_statement = "ORDER BY %s" % self.sort
            else:
                sort_statement = ""

            if self.where:
                where_statement = "WHERE %s" % self.where
            else:
                where_statement = ""
            self._tracks = self.get("SELECT DISTINCT %s FROM %s %s %s" %
                                    (",".join(self.fields),
                                     self.table,
                                     where_statement,
                                     sort_statement))
            columns = self.getColumns(self.table)
            self._slices = [x for x in columns
                            if x not in self.exclude_columns
                            and x not in self.fields] +\
                list(self.extra_columns.keys())
            # remove columns with special characters (:, +, -,)
            self._slices = [x for x in self._slices
                            if not re.search("[:+-]", x)]

            data = self.get("SELECT %s, %s FROM %s" %
                            (",".join(self.fields),
                             ",".join(self._slices),
                             self.table))
            self.data = odict()
            for d in data:
                tr = tuple(d[:nfields])
                self.data[tr] = odict(list(zip(self._slices,
                                               tuple(d[nfields:]))))
        self.loaded = True

    @property
    def tracks(self):
        if not self.hasTable(self.table):
            return []
        if not self.loaded:
            self._load()
        if len(self.fields) == 1:
            return tuple([x[0] for x in self._tracks])
        else:
            return tuple([tuple(x) for x in self._tracks])

    @property
    def slices(self):
        if not self.hasTable(self.table):
            return []
        if not self.loaded:
            self._load()
        return self._slices

    def __call__(self, track, slice=None):
        if not self.loaded:
            self._load()
        if len(self.fields) == 1:
            track = (track,)
        return self.data[track][slice]


class SingleTableTrackerColumns(TrackerSQL):

    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by:py:attr:`column` and one for a track.

    The tracks are derived from all columns in
    table:py:attr:`table`. By default, all columns are taken as tracks
    apart from:py:attr:`column` and those listed
    in:py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and
    ``human_counts``. The slices will be ``100``, ``200``, ``300``

    Tracker could be defined as::

       class MyTracker(SingleTableTrackerColumns):
          table = 'mytable'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    table = None
    column = None

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    @property
    def tracks(self):
        if not self.hasTable(self.table):
            return []
        columns = self.getColumns(self.table)
        return [x for x in columns
                if x not in self.exclude_columns and x != self.column]

    @property
    def slices(self):
        if self.column:
            return self.getValues("SELECT DISTINCT %(column)s FROM %(table)s")
        else:
            return []

    def __call__(self, track, slice=None):
        if slice is not None:
            data = self.getValue(
                "SELECT %(track)s FROM %(table)s WHERE %(column)s = '%(slice)s'")
        else:
            data = self.getValues("SELECT %(track)s FROM %(table)s")
        return data


class SingleTableTrackerEdgeList(TrackerSQL):

    '''Tracker returning values from a table with matrix type data
    that is stored in an edge list, for example::

         row   column    value
         A     B         1
         A     C         2
         B     C         3

    Returns a dictionary of values.

    The tracks are given by entries in the:py:attr:`row` column in a
    table:py:attr:`table`.  The slices are given by entries in the
    :py:attr:`column` column in a table.

    The:py:attr:`value` is a third column specifying the value
    returned. If:py:attr:`where` is set, it is added to the SQL
    statement to permit some filtering.

    If:py:attr:`transform` is set, it is applied to the value.

    if:py:attr:`value2` is set, the matrix is assumed to be stored in
    the format ``(row, column, value, value1)``, where ``value`` is
    the value for ``row,col`` and value2 is the value for ``col,row``.

    This method is inefficient, particularly so if there are no
    indices on:py:attr:`row` and:py:attr:`column`.


    '''
    table = None
    row = None
    column = None
    value = None
    value2 = None
    transform = None
    where = "1"

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    @property
    def tracks(self):
        if self.table is None:
            raise NotImplementedError("table not defined")
        if not self.hasTable(self.table):
            raise ValueError("unknown table %s" % self.table)

        if self.value2 is not None:
            return sorted(set(
                self.getValues("SELECT DISTINCT %(row)s FROM %(table)s") +
                self.getValues("SELECT DISTINCT %(column)s FROM %(table)s")))
        else:
            return self.getValues("SELECT DISTINCT %(row)s FROM %(table)s")

    @property
    def slices(self):
        if self.value2 is not None:
            return self.tracks
        else:
            return self.getValues("SELECT DISTINCT %(column)s FROM %(table)s")

    def __call__(self, track, slice=None):

        try:
            val = self.getValue("""SELECT %(value)s FROM %(table)s
            WHERE %(row)s = '%(track)s' AND
            %(column)s = '%(slice)s' AND %(where)s""")
        except exc.SQLAlchemyError:
            val = None

        if val is None and self.value2:
            try:
                val = self.getValue(
                    """SELECT %(value2)s FROM %(table)s
                    WHERE %(row)s = '%(slice)s' AND
                    %(column)s = '%(track)s' AND %(where)s""")
            except exc.SQLAlchemyError:
                val = None

        if val is None:
            return val

        if self.transform:
            return self.transform(val)
        return val


class SingleTableTrackerEdgeListToMatrix(TrackerSQL):

    '''Tracker returning values from a table with matrix type data
    that is stored in an edge list, for example::

         row   column    value
         A     B         1
         A     C         2
         B     C         3

    Returns a numpy matrix.

    The tracks are given by entries in the:py:attr:`row` column in a
    table:py:attr:`table`.  The slices are given by entries in the
    :py:attr:`column` column in a table.

    The:py:attr:`value` is a third column specifying the value
    returned. If:py:attr:`where` is set, it is added to the SQL
    statement to permit some filtering.

    If:py:attr:`transform` is set, it is applied to the value.

    if:py:attr:`value2` is set, the matrix is assumed to be stored in
    the format ``(row, column, value, value1)``, where ``value`` is
    the value for ``row,col`` and value2 is the value for ``col,row``.
    '''
    table = None
    row = None
    column = None
    value = None
    value2 = None
    missing_value = 0
    diagonal_value = 0
    # set to true if matrix is symmetric
    is_symmetric = False
    dtype = numpy.int
    where = "1"

    # saved by preloading 
    _matrix = None
    _rows = None
    _cols = None

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def getTracks(self):
        self._load()
        return self._rows

    def getSlices(self):
        self._load()
        return self._cols

    def _load(self):
        '''load data.

        The data is pre-loaded in order to avoid multiple random access
        operations on the same table.
        '''
        if self._matrix is None:
            if self.value2 is None:
                data = self.get(
                    "SELECT %(row)s, %(column)s, %(value)s "
                    "FROM %(table)s WHERE %(where)s")
            else:
                data = self.get(
                    "SELECT %(row)s, %(column)s, %(value)s, %(value2)s "
                    "FROM %(table)s WHERE %(where)s")

            self._matrix, self._rows, self._cols = \
                Stats.buildMatrixFromEdges(
                    data,
                    is_symmetric=self.is_symmetric,
                    missing_value=self.missing_value,
                    diagonal_value=self.diagonal_value,
                    dtype=self.dtype)
            self._map_rows = dict([(y, x) for x, y in enumerate(self._rows)])
            self._map_cols = dict([(y, x) for x, y in enumerate(self._cols)])

    def __call__(self, track, slice):
        self._load()
        return self._matrix[self._map_rows[track], self._map_cols[slice]]


class MultipleTableTrackerEdgeList(TrackerSQL):

    '''Tracker representing multiple tables with matrix type data.

    Returns a dictionary of values.

    The tracks are given by table names mathing:py:attr:`pattern`.
    '''
    row = None
    column = None
    value = None
    as_tables = True

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def __call__(self, track, slice=None):

        if self.column is None:
            raise ValueError('MultipleTrackerEdgeList requires a column field')
        if self.row is None:
            raise ValueError('MultipleTrackerEdgeList requires a row field')
        if self.value is None:
            raise ValueError('MultipleTrackerEdgeList requires a value field')

        data = self.get("""SELECT %(row)s, %(column)s, %(value)s
                            FROM %(track)s
                            ORDER BY fdr,power""")
        result = odict()
        for row, col, value in data:
            try:
                result[row][col] = value
            except KeyError:
                result[row] = odict()
                result[row][col] = value

        return result


class SingleTableTrackerHistogram(TrackerSQL):

    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by:py:attr:`column` and one for a track.

    The tracks are derived from all columns in
    table:py:attr:`table`. By default, all columns are taken as tracks
    apart from:py:attr:`column` and those listed
    in:py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and
    ``human_counts``. The Tracker could be defined as::

       class MyTracker(SingleTableTrackerHistogram):
          table = 'mytable'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    table = None
    column = None
    value = 'data'

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    @property
    def tracks(self):

        if self.column is None:
            raise NotImplementedError(
                "column not set - Tracker not fully implemented")
        if not self.hasTable(self.table):
            return []
        columns = self.getColumns(self.table)
        return [x for x in columns
                if x not in self.exclude_columns and x != self.column]

    def __call__(self, track, slice=None):
        if self.column is None:
            raise NotImplementedError(
                "column not set - Tracker not fully implemented")
        # labels need to be consistent in order
        # so rename track to value.
        data = self.getAll(
            "SELECT %(column)s, %(track)s AS %(value)s FROM %(table)s")
        return data


class MultipleTableTrackerHistogram(TrackerSQL):

    '''Tracker representing multiple table with multiple slices.

    Returns a dictionary of two sets of data, one given
    by:py:attr:`column` and one for a track.

    The tracks are derived from all columns in
    table:py:attr:`table`. By default, all columns are taken as tracks
    apart from:py:attr:`column` and those listed
    in:py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and
    ``human_counts``. The Tracker could be defined as::

       class MyTracker(ManyTableTrackerHistogram):
          pattern = '(.*)_table'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    as_tables = True
    column = None

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    @property
    def slices(self):
        if self.column == None:
            raise NotImplementedError(
                "column not set - Tracker not fully implemented")
        columns = set()
        for table in self.getTableNames(self.pattern):
            columns.update(self.getColumns(table))
        return [x for x in columns if x not in self.exclude_columns and x != self.column]

    def __call__(self, track, slice):
        # check if column exists in particular table - if not, return no data
        if slice not in self.getColumns(track):
            return None

        return self.getAll("""SELECT %(column)s, %(slice)s FROM %(track)s""")

    # def __call__(self, track):

    #     if self.column == None: raise NotImplementedError("column not set - Tracker not fully implemented")
    # get columns in the alphabetical order
    #     columns = sorted(self.getColumns(track) )
    #     if self.column not in columns: raise ValueError("column '%s' missing from '%s'" % (self.column, track))
    #     columns = ",".join([ x for x in columns if x not in self.exclude_columns and x != self.column ])
    # return self.getAll("""SELECT %(column)s, %(columns)s FROM %(track)s""")


class TrackerSQLMulti(TrackerSQL):

    '''An SQL tracker spanning multiple databases.

    '''

    databases = ()
    tracks = ()

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

        if len(self.tracks) == 0:
            raise ValueError("no tracks specified in TrackerSQLMulti")
        if (len(self.tracks) != len(self.databases)):
            raise ValueError(
                "TrackerSQLMulti requires an equal number of "
                "tracks (%i) and databases (%i)"
                % (len(self.tracks), len(self.databases)))
        if not self.backend.startswith("sqlite"):
            raise ValueError("TrackerSQLMulti only works for sqlite database")

        if not self.db:
            def _my_creator():
                # issuing the ATTACH DATABASE into the sqlalchemy ORM
                # (self.db.execute(...))  does not work. The database
                # is attached, but tables are not accessible in later
                # SELECT statements.
                import sqlite3
                conn = sqlite3.connect(re.sub("sqlite:///", "", self.backend))
                for track, name in zip(self.databases, self.tracks):
                    conn.execute("ATTACH DATABASE '%s/csvdb' AS %s" %
                                 (os.path.abspath(track),
                                  name))
                return conn

            self.connect(creator=_my_creator)


class TrackerMultipleLists(TrackerSQL):

    '''A class to retrieve multiple columns across one or more tables.
    Returns a dictionary of lists.

    TrackerMultipleLists can be used in conjunction with venn and
    hypergeometric transformers and the venn render.

    The items in each list are specified by an SQL statement. The
    statements can be specified in 3 different ways:

    :attr:`statements` dictionary
        If the tracker contains a statements attribute then the statments
        are taken from here as well as the list names e.g.::

        class TrackerOverlapTest1(TrackerOverlappingSets):
            statements = {"listA": "SELECT gene_id FROM table_a",
                          "listB": "SELECT gene_id FROM table_b"}

    :attr:`listA`,:attr:`listB`,:attr:`listC` and:attr:`background` attributes

        If the tracker does not contain a statements dictionary then
        the statements can be specifed using these attributes. An
        optional list of labels can be specified for the names of
        these lists. For example::

            class TrackerOverlapTest2(TrackerOverlappingSets):
               listA = "SELECT gene_id FROM table_a"
               listB = "SELECT gene_id FROM table_b"

               labels = ["FirstList","SecondList"]

    :meth:`getStatements` method

         The:meth:`getStatements` method can be overridden to allow
         full control over where the statements come from. It should
         return a dictionary of SQL statements.

    Because TrackerMultipleLists is derived from:class:`TrackerSQL`,
    tracks and slices can be specified in the usual way.

    '''

    statements = None
    ListA = None
    ListB = None
    ListC = None
    background = None
    labels = None

    def getStatements(self):

        statements = odict()

        if self.statements:
            return self.statements

        if self.ListA:
            if self.labels:
                label = self.labels[0]
            else:
                label = "ListA"
            statements[label] = self.ListA

        if self.ListB:

            if self.labels:
                label = self.labels[1]
            else:
                label = "ListB"

            statements[label] = self.ListB

        if self.ListC:

            if self.labels:
                label = self.labels[2]
            else:
                label = "ListC"

            statements[label] = self.ListC

        if self.background:
            statements["background"] = self.background

        return statements

    def __call__(self, track, slice=None):

        statements = self.getStatements()
        # track and slice will be substituted in the statements
        return odict([(
            x, 
            self.getValues(statements[x])) for x in statements])


class MeltedTableTracker(TrackerSQL):

    '''Tracker representing multiple tables with the same columns.

    The tables are melted - a column called ``track`` is added
    that contains the table name (see :py:attr:`column_name`)

    '''
    tracks = "all"
    pattern = None
    column_name = 'track'

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def __call__(self, track):
        assert(self.pattern is not None)
        tables = self.getTables(self.pattern)

        if len(tables) == 0:
            return None

        ref_columns = self.getColumns(tables[0])
        fields = ",".join(ref_columns)
        results = []
        for table in tables:
            columns = self.getColumns(table)
            if columns != ref_columns:
                warnings.warn(
                    "incompatible column names in table %s - skipped" % table)
                continue

            track = re.search(self.pattern, table).groups()[0]

            results.extend(
                self.get(
                    "SELECT '%(track)s' as track, %(fields)s FROM %(table)s"))

        ref_columns.insert(0, self.column_name)

        return odict(list(zip(ref_columns, list(zip(*results)))))


class MeltedTableTrackerDataframe(MeltedTableTracker):

    '''Tracker representing multiple tables with the same columns.

    The tables are melted - a column called ``track`` is added
    that contains the table name.

    This tracker returns a dataframe directly.
    '''
    tracks = "all"
    pattern = None

    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs)

    def __call__(self, track):
        data = MeltedTableTracker.__call__(self, track)
        return pandas.DataFrame.from_dict(data)
