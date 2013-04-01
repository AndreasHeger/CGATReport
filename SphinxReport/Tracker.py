import os, sys, re, types, copy, warnings, inspect, logging, glob

# Python 2/3 Compatibility
try: import ConfigParser as configparser
except: import configparser

import numpy

import sqlalchemy
import sqlalchemy.exc as exc
import sqlalchemy.engine

# for rpy2 for data frames
import rpy2
from rpy2.robjects import r as R

from SphinxReport import Utils

from collections import OrderedDict as odict
import collections

class SQLError( Exception ):
    pass

###########################################################################
###########################################################################
###########################################################################
def prettyFloat( val, format = "%5.2f" ):
    """output a float or "na" if not defined"""
    try:
        x = format % val
    except (ValueError, TypeError):
        x = "na"
    return x
    
###########################################################################
###########################################################################
###########################################################################
def prettyPercent( numerator, denominator, format = "%5.2f" ):
    """output a percent value or "na" if not defined"""
    try:
        x = format % (100.0 * numerator / denominator )
    except (ValueError, ZeroDivisionError):
        x = "na"
    return x

###########################################################################
###########################################################################
###########################################################################
def getCallerLocals( level = 3, decorators = 0):
    '''returns locals of caller using frame.

    optional pass number of decorators
    
    from http://pylab.blogspot.com/2009/02/python-accessing-caller-locals-from.html
    '''
    f = sys._getframe(level+decorators)
    args = inspect.getargvalues(f)
    return args[3]

def quoteField( s ):
    '''returns a quoted version of s for inclusion in SQL statements.'''
    # replace internal "'" with "\'"
    return re.sub( "'", "''", s)


###########################################################################
###########################################################################
###########################################################################
@Utils.memoized
def getTableNames( db ):
    '''return a set of table names.'''
    inspector = sqlalchemy.engine.reflection.Inspector.from_engine(db) 
    return set(inspector.get_table_names())

###########################################################################
###########################################################################
###########################################################################
def getTableColumns( db, tablename ):
    '''return a list of columns for table *tablename*.'''
    inspector = sqlalchemy.engine.reflection.Inspector.from_engine(db) 
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        vals = inspector.get_columns(tablename)
    return vals
    
###########################################################################
###########################################################################
###########################################################################
class Tracker(object):
    """
    Base class for trackers. User trackers should be derived from this class.

    A tracker provides the data for a given :term:`track` through
    its __call__ method. Optionally, the data can be sliced, with
    a :term:`slice` containing a subset of the data.

    For example, tracks could be 
    entities like cars, motorcycles, and bikes, and slices could
    be colours like blue, red, green::

       class LengthTracker( Tracker ):
          mData = ...
          def __call__( self, track, slice ):
             return [x.length for x in mData if x.type == track and x.color == slice]

    The call::

       tracker = LengthTracker()
       tracker("car", "blue")

    would return the lengths of blue cars.
    """

    mMinData = 1

    # set to False, if results of tracker should be cached
    cache = True

    # default: empty tracks/slices
    # tracks = []
    # slices = []
    # paths = []

    def __init__(self, *args, **kwargs):
        pass

    # def getTracks( self ):
    #     """return a list of all tracks that this tracker provides."""
    #     return self.tracks

    # def getSlices( self ):
    #     """return a list of all slices that this tracker provides.
    #     """
    #     return self.slices

    # def getPaths( self ):
    #     """return all paths this tracker provides.
    #     """
    #     return self.paths

    def getShortCaption( self ):
        """return one line caption.

        The default is to return the first non-blank line of the __doc__ string.
        """
        try:
            for line in self.__doc__.split("\n"):
                if line.strip(): return line.strip()
        except AttributeError:
            return ""
        return ""

    def __call__(self, track, slice = None):
        """return a data structure for track :param: track and slice :slice:"""
        raise NotImplementedError("Tracker not fully implemented -> __call__ missing")

    def members( self, locals = None ):
        '''function similar to locals() but returning member variables of this tracker.

        Convenience function for string substitution. If *locals* is given (and a dictionary),
        the dictionary is added to the returned dictionary. Entries in *local* take precedence
        before member variables.

        Typical usage is::

           print "my string with %(vars)s" % (self.members(locals())).

        returns a dictionary
        '''
        # skip tracks and slices to avoid recursion
        # todo: do this for the general case
        # 1. subtract property attributes, or
        # 2. subtract members of Tracker()
        l = dict( [(attr,getattr(self,attr)) for attr in dir(self) \
                      if not isinstance(attr, collections.Callable) and not attr.startswith("__") and attr != "tracks" and attr != "slices"] )
            
        if locals: return dict( l, **locals)
        else: return l

###########################################################################
###########################################################################
###########################################################################
class TrackerTSV( Tracker ):
    """Base class for trackers that fetch data from an CSV file.

    Each track is a column in the file.
    """
    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )
        if "tracker" not in kwargs:
            raise ValueError( "TrackerTSV requires a :tracker: parameter" )
        
        self.filename = kwargs['tracker'].strip()
        self._data = None
        self._tracks = None

    def getTracks(self, subset = None ):
        if self.filename.endswith( ".gz" ):
            inf = gzip.open( self.filename, "r" )
        else:
            inf = open( self.filename, "r" )

        for line in inf:
            if line.startswith("#"): continue
            tracks = line[:-1].split( "\t" )
            break
        inf.close()
        self._tracks = tracks
        return tracks
    
    def readData( self ):
        if self._data == None:
            if self.filename.endswith( ".gz" ):
                inf = gzip.open( self.filename, "r" )
            else:
                inf = open( self.filename, "r" )

            data = [ x.split() for x in inf.readlines() if not x.startswith("#")]
            inf.close()

            self.data = dict( list(zip( data[0], list(zip( *data[1:] )) )) )

    def __call__(self, track, **kwargs ):
        """return a data structure for track :param: track"""
        self.readData()
        return self.data[track]

class TrackerMatrix( TrackerTSV ):
    """Return matrix data from a matrix in flat-file format.
    """
    def getTracks(self, subset = None ):
        return glob.glob( self.glob )

    def __init__(self, *args, **kwargs ):
        TrackerTSV.__init__(self, *args, **kwargs )
        self.glob = kwargs['tracker'].strip()

    def __call__(self, track, **kwargs ):
        """return a data structure for track :param: track"""
        
        if track.endswith( ".gz" ):
            infile = gzip.open( track, "r" )
        else:
            infile = open( track, "r" )
        
        dtype = numpy.float

        lines = [ l for l in infile.readlines() if not l.startswith("#") ]
        infile.close()
        nrows = len(lines) - 1
        col_headers = lines[0][:-1].split("\t")[1:]
        ncols = len(col_headers)
        matrix = numpy.zeros( (nrows, ncols), dtype = dtype )
        row_headers = []
        
        for row, l in enumerate(lines[1:]):
            data = l.split("\t")
            row_headers.append( data[0] )
            matrix[row] = numpy.array(data[1:], dtype = dtype)
        
        return odict( ( ('matrix', matrix),
                        ('rows', row_headers),
                        ('columns', col_headers) ) )

###########################################################################
###########################################################################
###########################################################################
class TrackerImages( Tracker ):
    '''Collect image files and arrange them in a gallery.
    '''
    
    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )
        if "tracker" not in kwargs:
            raise ValueError( "TrackerImages requires a :tracker: parameter" )
        self.glob = kwargs["tracker"]

    def getTracks(self, subset = None ):
        return glob.glob( self.glob )
    
    def __call__(self, track, **kwargs ):
        """return a data structure for track :param: track and slice :slice:"""
        return odict( ( ('name', track), ( 'filename', track) ) )

###########################################################################
###########################################################################
###########################################################################
class TrackerSQL( Tracker ):
    """Base class for trackers that fetch data from an SQL database.
    
    The basic tracker identifies tracks as tables that match a
    certain pattern (:attr:`pattern`)

    The pattern should contain at least one group. If there are multiple
    groups, these will be associated as tracks/slices.

    This tracker connects to the database. Each tracker will establish
    its own connection for efficient multi-processing.

    If :attr:`as_tables` is set, the full table names will be returned.
    The default is to apply :attr:`pattern` and return the result.
    """

    pattern = None
    as_tables = False

    def __init__(self, backend = None, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )

        # connection within python
        self.db = None

        # connection within R
        self.rdb = None

        if backend != None:
            # backend given - use it
            self.backend = backend
        else:
            # not defined previously (by mix-in class) get default
            if not hasattr( self, "backend" ):
                self.backend = Utils.PARAMS["report_sql_backend"]

        # patch for mPattern and mAsTables for backwards-compatibility
        if hasattr( self, "mPattern"):
            warnings.warn( "mPattern is deprecated, use pattern instead", DeprecationWarning )
            self.pattern = "(.*)%s" % self.mPattern
        if hasattr( self, "mAsTables" ):
            warnings.warn( "mAsTables is deprecated, use as_tables instead", DeprecationWarning )
            self.as_tables = self.mAsTables

    def connect( self, creator = None ):
        """lazy connection function."""

        if not self.db:
            
            logging.debug( "connecting to %s" % self.backend )

            # creator can not be None.
            if creator:
                db = sqlalchemy.create_engine( self.backend, 
                                               echo = False,
                                               creator = creator )
            else:
                db = sqlalchemy.create_engine( self.backend, 
                                               echo = False )
            
            if not db:
                raise ValueError( "could not connect to database %s" % self.backend )

            db.echo = False  

            # ignore unknown type BigInt warnings
            # Note that this step can take a while on large databases
            # with many tables and many columns
            if db and False:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.metadata = sqlalchemy.MetaData(db, reflect = True)
                except AttributeError:
                    self.metadata = sqlalchemy.MetaData(db, reflect = True)

            self.db = db

            logging.debug( "connected to %s" % self.backend )

    def rconnect( self ):
        '''open connection within R to database.'''

        if not self.rdb:
            if self.backend.startswith( 'sqlite' ):
                R.library( 'RSQLite' )
                self.rdb = R.dbConnect(R.SQLite(), dbname=re.sub( "sqlite:///./", "", self.backend ) )
            else:
                raise NotImplementedError("can not connect to %s in R" % self.backend )


    def getTables(self, pattern = None ):
        """return a list of tables matching a *pattern*.

        This function does not return table views.

        returns a list of table objects.
        """
        self.connect()
        sorted_tables = sorted(getTableNames( self.db ))

        if pattern:
            rx = re.compile(pattern)
            return [ x for x in sorted_tables if rx.search( x ) ]
        else:
            return sorted_tables

    def getTableNames( self, pattern = None ):
        '''return a list of tablenames matching a *pattern*.
        '''
        return self.getTables( pattern )

    def hasTable( self, tablename ):
        """return table with name *tablename*."""
        self.connect()
        return tablename in getTableNames( self.db )

    def getColumns( self, tablename ):
        '''return a list of columns in table *tablename*.'''
        
        self.connect()
        columns = getTableColumns( self.db, tablename )
        return [ re.sub( "%s[.]" % tablename, "", x['name']) for x in columns ]

    def execute(self, stmt ):
        self.connect()
        try:
            r = self.db.execute(stmt)
        except exc.SQLAlchemyError as msg:
            raise SQLError(msg)
        return r

    def buildStatement( self, stmt ):
        '''fill in placeholders in stmt.'''
        
        kwargs = self.members( getCallerLocals() )
        statement = stmt % dict( list(kwargs.items()) )
        return statement

    def getValue( self, stmt ):
        """returns a single value from SQL statement *stmt*.

        The SQL statement is subjected to variable interpolation.

        This function will return the first value in the first row
        from a SELECT statement.
        """
        statement = self.buildStatement(stmt)
        result = self.execute(statement).fetchone()
        if result == None:
            raise exc.SQLAlchemyError( "no result from %s" % statement )
        return result[0]

    def getFirstRow( self, stmt ):
        """return a row of values from SQL statement *stmt* as a list.

        The SQL statement is subjected to variable interpolation.

        This function will return the first row from a SELECT statement
        as a list.

        Returns None if result is empty.
        """
        e = self.execute(self.buildStatement(stmt)).fetchone()
        if e: return list(e)
        else: return None

    def getRow( self, stmt ):
        """return a row of values from an SQL statement as dictionary.

        This function will return the first row from a SELECT 
        statement as a dictionary of column-value mappings.

        Returns None if result is empty.
        """
        e = self.execute( self.buildStatement( stmt )).fetchone()
        # assumes that values are sorted in ResultProxy.keys()
        if e: return odict( [x,e[x]] for x in list(e.keys()) )
        else: return None

    def getValues( self, stmt ):
        """return values from SQL statement *stmt* as a list.

        This function will return the first value in each row
        from an SELECT statement.

        Returns an empty list if there is no result.
        """
        e = self.execute(self.buildStatement(stmt)).fetchall()
        if e: return [x[0] for x in e]
        return []

    def getAll( self, stmt ):
        """return all rows from SQL statement *stmt* as a dictionary.

        The dictionary contains key/values pairs where keys are
        the selected columns and the values are the results.

        Example: SELECT column1, column2 FROM table
        Example: { 'column1': [1,2,3], 'column2' : [2,4,2] }

        Returns an empty dictionary if there is no result.
        """
        # convert to tuples
        e = self.execute(self.buildStatement(stmt))
        columns = list(e.keys())
        d = e.fetchall()
        return odict( list(zip( columns, list(zip( *d )) )) )

    def get( self, stmt ):
        """return all results from an SQL statement as list of tuples.

        Example: SELECT column1, column2 FROM table
        Result: [(1,2),(2,4),(3,2)]

        Returns an empty list if there is no result.
        """
        return self.execute(self.buildStatement(stmt)).fetchall()

    def getDict( self, stmt ):
        """return results from SQL statement *stmt* as a dictionary.

        Example: SELECT column1, column2 FROM table
        Result: { 1: 2, 2: 4, 3: 2}

        The first column is taken as the dictionary key
        """
        # convert to tuples
        e = self.execute(self.buildStatement(stmt))
        columns = list(e.keys())
        result = odict()
        for row in e:
            result[row[0]] = odict( list(zip( columns[1:], row[1:] )) )
        return result

    def getIter( self, stmt ):
        '''returns an iterator over results of SQL statement *stmt*.
        '''
        return self.execute(stmt)
    
    def getTracks(self, *args, **kwargs):
        """return a list of all tracks that this tracker provides.

        Tracks are defined as tables matching the attribute 
        :attr:`pattern`.
        """
        if self.pattern:
            rx = re.compile(self.pattern)
            tables = self.getTables( pattern = self.pattern )
            if self.as_tables:
                return sorted([ x for x in tables ] )
            else: 
                return sorted([rx.search(x).groups()[0] for x in tables] )
        else:
            return [ "all" ] 

    def getDataFrame( self, stmt ):
        '''return an R data frame as rpy2 object.
        '''
        self.rconnect()
        return R.dbGetQuery(self.rdb, self.buildStatement(stmt) )
    
    def getPaths( self ):
         """return all paths this tracker provides.

         Tracks are defined as tables matching the attribute 
         :attr:`pattern`. 

         """
         if self.pattern:
            rx = re.compile(self.pattern)
            # let getTracks handle a single group
            if rx.groups < 2: return None
            tables = self.getTables( pattern = self.pattern )
            parts = [rx.search(x).groups() for x in tables]
            result = []
            for x in range(rx.groups):
                result.append( sorted( set( [ part[x] for part in parts ] ) ) )
            return result
         return None
         

###########################################################################
###########################################################################
###########################################################################

class TrackerSQLCheckTables(TrackerSQL):
    """Tracker that examines the presence/absence of a certain
    field in a list of tables.

    Define the following attributes:

    :attr:`mFields` fields to join
    :attr:`mExcludePattern`: tables to exclude
    :attr:`pattern`: pattern to define tracks (see :class:`TrackerSql`)
    """

    mFields = ["id",]
    mExcludePattern = None
    pattern = "_annotations$"
    mIncludePattern = "^%s_"

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    def getSlices(self, subset = None):
        return self.mFields

    def getTablesOfInterest( self, track ):

        if self.mExcludePattern: 
            keep = lambda x: not re.search( self.mExcludePattern, x ) and re.search( self.mIncludePattern % track, x )
        else:
            keep = lambda x: re.search( self.mIncludePattern % track, x )

        return [ x for x in self.getTables() if keep(x.name) ]
        
    def __call__(self, track, slice = None):
        """count number of unique occurances of field *slice* in tables matching *track*."""

        tables = self.getTablesOfInterest( track )
        data = []
        for table in tables:
            if slice not in [x.name for x in table.columns]: continue
            # remove the table name and strip offensive characters
            field = re.sub( self.mIncludePattern % track, "", table.name ).strip( "._:@$!?#")
            data.append( (field,
                          self.getValue( "SELECT COUNT(DISTINCT %s) FROM %s" % (slice, table.name) ) ) )
        return odict( data )
        
###########################################################################
###########################################################################
###########################################################################

class TrackerSQLCheckTable(TrackerSQL):
    """Tracker that counts existing entries in a table.

    Define the following attributes:
    :attr:`mExcludePattern`: columns to exclude
    :attr:`pattern`: pattern to define tracks (see :class:`TrackerSql`)
    """

    mExcludePattern = None
    pattern = "(.*)_evol$"
    
    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    def __call__(self, track, *args ):
        """count number of entries in a table."""

        statement = "SELECT COUNT( %s) FROM %s WHERE %s IS NOT NULL" 

        if self.mExcludePattern: 
            fskip = lambda x: re.search( self.mExcludePattern, x )
        else:
            fskip = lambda x: False

        tablename = track + "_evol" 
        columns = self.getColumns( tablename )
        data = []
            
        for column in columns:
            if fskip( column ): continue
            data.append( (column, self.getValue( statement % (column, tablename, column) ) ) )
        return odict( data )

###########################################################################
###########################################################################
###########################################################################

class Config( Tracker ):
    '''Tracker providing config values of ini files.

    The .ini files need to be located in the directory
    from which sphinxreport is called.

    returns a dictionary of key,value pairs.
    '''
    tracks = glob.glob( "*.ini" )

    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )

    def __call__(self, track, *args ):
        """count number of entries in a table."""

        config = configparser.ConfigParser()
        config.readfp(open(track),"r")

        result = odict()

        def convert( value ):
            '''convert a value to int, float or str.'''
            rx_int = re.compile("^\s*[+-]*[0-9]+\s*$")
            rx_float = re.compile("^\s*[+-]*[0-9.]+[.+\-eE][+-]*[0-9.]*\s*$")

            if value == None: return value

            if rx_int.match( value ):
                return int(value), "int"
            elif rx_float.match( value ):
                return float(value), "float"
            return value, "string"

        for section in config.sections():
            x = odict()
            for key,value in config.items( section ):
                x[key] = odict( list(zip( ("value", "type" ), convert( value ))) )
            result[section] = x
        
        return result

###########################################################################
###########################################################################
###########################################################################
        
class Empty( Tracker ):
    '''Empty tracker

    This tracker servers as placeholder for plots that require no input from a tracker.
    '''

    def getTracks( self, subset = None ):
        """return a list of all tracks that this tracker provides."""
        if subset: return subset
        return ["empty"]

    def __call__(self, *args ):
        return odict( (("a", 1),))

###########################################################################
###########################################################################
###########################################################################
class Status( TrackerSQL ):
    '''Tracker returning status information.
    
    Define tracks and slices. Slices will be translated into
    calls to member functions starting with 'test'. 

    Each test function should return a tuple with the test
    status and some information.
    
    If this tracker is paired with a :class:`Renderer.Status`
    renderer, the following values of a test status will be
    translated into icons: ``PASS``, ``FAIL``, ``WARNING``, ``NOT AVAILABLE``.
    
    The docstring of the test function is used as description.
    '''

    def getSlices( self, subset = None ):
        return [ x[4:] for x in dir(self) if x.startswith("test")]
        
    def __call__(self, track, slice ):
        if not hasattr( self, "test%s" % slice ):
            raise NotImplementedError( "test%s not implement" % slice )
        
        status, value = getattr( self, "test%s" % slice )(track)
        description = getattr( self, "test%s" % slice ).__doc__
        
        return odict( 
            (( 'status', status),
             ( 'info', str(value)),
             ( 'description', description ) ) )
    
###########################################################################
###########################################################################
###########################################################################
class SingleTableTrackerRows( TrackerSQL ):
    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of values.

    The tracks are given by rows in table :py:attr:`table`. The tracks are
    specified by the :py:attr:`fields`. 

    :py:attr:`fields` is a tuple of column names (default = ``(track,)``).

    If multiple columns are specified, they will all be used to define the 
    tracks in the table.

    Rows in the table need to be unique for any combination :py:attr:`fields`.

    attribute:`extra_columns` can be used to add additional columns to the table.
    This attribute is a dictionary.
    '''
    exclude_columns = ()
    table = None
    fields = ("track",)
    extra_columns = {}
    sort = None
    loaded = False

    # not called by default as Mixin class
    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    def _load(self):
        '''load data.

        The data is pre-loaded in order to avoid multiple random access 
        operations on the same table.
        '''
        if not self.loaded:
            nfields = len(self.fields)
            if self.sort: sort = "ORDER BY %s" % self.sort
            else: sort = ""
            self._tracks = self.get( "SELECT DISTINCT %s FROM %s %s" % \
                                         (",".join(self.fields), self.table, sort ))
            columns = self.getColumns( self.table ) 
            self._slices = [ x for x in columns if x not in self.exclude_columns and x not in self.fields ] + list(self.extra_columns.keys())
            # remove columns with special characters (:, +, -, )
            self._slices = [ x for x in self._slices if not re.search( "[:+-]", x)]

            data = self.get( "SELECT %s, %s FROM %s" %
                             (",".join(self.fields), ",".join(self._slices), self.table))
            self.data = odict()
            for d in data:
                tr = tuple(d[:nfields])
                self.data[tr] = odict( list(zip( self._slices, tuple(d[nfields:]))) )
            self.loaded = True

    @property
    def tracks( self ):
        if not self.hasTable( self.table ): return []
        if not self.loaded: self._load()
        if len(self.fields) == 1:
            return tuple( [x[0] for x in self._tracks ] )
        else:
            return tuple( [tuple(x) for x in self._tracks ] )

    @property
    def slices( self ):
        if not self.hasTable( self.table ): return []
        if not self.loaded: self._load()
        return self._slices

    def __call__(self, track, slice = None ):
        if not self.loaded: self._load()
        if len(self.fields) == 1: track = (track,)
        return self.data[track][slice]

###########################################################################
###########################################################################
###########################################################################
class SingleTableTrackerColumns( TrackerSQL ):
    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by :py:attr:`column` and one for a track.

    The tracks are derived from all columns in table :py:attr:`table`. By default,
    all columns are taken as tracks apart from :py:attr:`column` and those
    listed in :py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and ``human_counts``. The slices
    will be ``100``, ``200``, ``300``

    Tracker could be defined as::
 
       class MyTracker( SingleTableTrackerColumns ):
          table = 'mytable'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    table = None
    column = None

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    @property
    def tracks(self):
        if not self.hasTable( self.table ): return []
        columns = self.getColumns( self.table )
        return [ x for x in columns if x not in self.exclude_columns and x != self.column ]

    @property
    def slices(self):
        if self.column:
            return self.getValues( "SELECT DISTINCT %(column)s FROM %(table)s" )
        else:
            return []

    def __call__(self, track, slice = None ):
        if slice != None:
            data = self.getValue( "SELECT %(track)s FROM %(table)s WHERE %(column)s = '%(slice)s'" )
        else:
            data = self.getValues( "SELECT %(track)s FROM %(table)s" )
        return data

###########################################################################
###########################################################################
###########################################################################
class SingleTableTrackerHistogram( TrackerSQL ): 
    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by :py:attr:`column` and one for a track.

    The tracks are derived from all columns in table :py:attr:`table`. By default,
    all columns are taken as tracks apart from :py:attr:`column` and those
    listed in :py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and ``human_counts``. The 
    Tracker could be defined as::
 
       class MyTracker( SingleTableTrackerHistogram ):
          table = 'mytable'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    table = None
    column = None

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    @property
    def tracks(self):
        if self.column == None: raise NotImplementedError( "column not set - Tracker not fully implemented" )
        if not self.hasTable( self.table ): return []
        columns = self.getColumns( self.table )
        return [ x for x in columns if x not in self.exclude_columns and x != self.column ]

    def __call__(self, track, slice = None ):
        if self.column == None: raise NotImplementedError( "column not set - Tracker not fully implemented" )
        data = self.getAll( "SELECT %(column)s, %(track)s FROM %(table)s" )
        return data

class MultipleTableTrackerHistogram( TrackerSQL ): 
    '''Tracker representing multiple table with multiple slicel.

    Returns a dictionary of two sets of data, one given
    by :py:attr:`column` and one for a track.

    The tracks are derived from all columns in table :py:attr:`table`. By default,
    all columns are taken as tracks apart from :py:attr:`column` and those
    listed in :py:attr:`exclude_columns`.

    An example for a table using this tracker would be::

       bin   mouse_counts    human_counts
       100   10              10
       200   20              15
       300   10              4

    In the example above, the tracks will be ``mouse_counts`` and ``human_counts``. The 
    Tracker could be defined as::
 
       class MyTracker( ManyTableTrackerHistogram ):
          pattern = '(.*)_table'
          column = 'bin'

    '''
    exclude_columns = ("track,")
    as_tables = True
    column = None

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    @property
    def slices(self):
        if self.column == None: raise NotImplementedError( "column not set - Tracker not fully implemented" )
        columns = set()
        for table in self.getTableNames( self.pattern ):
            columns.update( self.getColumns( table ) )
        return [ x for x in columns if x not in self.exclude_columns and x != self.column ]

    def __call__(self, track, slice ):
        # check if column exists in particular table - if not, return no data
        if slice not in self.getColumns( track ):
            return None
        
        return self.getAll( """SELECT %(column)s, %(slice)s FROM %(track)s""" )

    # def __call__(self, track ):
        
    #     if self.column == None: raise NotImplementedError( "column not set - Tracker not fully implemented" )
    #     # get columns in the alphabetical order
    #     columns = sorted( self.getColumns( track ) )
    #     if self.column not in columns: raise ValueError("column '%s' missing from '%s'" % (self.column, track ))
    #     columns = ",".join( [ x for x in columns if x not in self.exclude_columns and x != self.column ] )
    #     return self.getAll( """SELECT %(column)s, %(columns)s FROM %(track)s""" )


###########################################################################
###########################################################################
###########################################################################
class SingleTableTrackerEdgeList( TrackerSQL ):
    '''Tracker representing a table with matrix type data.

    Returns a dictionary of values.

    The tracks are given by entries in the :py:attr:`row` column in a table :py:attr:`table`. 
    The slices are given by entries in the :py:attr:`column` column in a table.

    The :py:attr:`fields` is a third column specifying the value returned. If :py:attr:`where`
    is set, it is added to the SQL statement to permit some filtering.

    If :py:attr:`transform` is set, it is applied to the value.

    This method is inefficient, particularly so if there are no indices on :py:attr:`row` and :py:attr:`column`.

    '''
    table = None
    row = None
    column = None
    value = None
    transform = None
    where = "1"

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    @property
    def tracks( self ):
        if not self.hasTable( self.table ): return []
        return [ x[0] for x in self.get( "SELECT DISTINCT %s FROM %s" % (self.row, self.table )) ]

    @property
    def slices( self ):
        if not self.hasTable( self.table ): return []
        return [ x[0] for x in self.get( "SELECT DISTINCT %s FROM %s" % (self.row, self.table )) ]

    def __call__(self, track, slice = None ):
        try:
            val = self.getValue( "SELECT %(value)s FROM %(table)s WHERE %(row)s = '%(track)s' AND %(column)s = '%(slice)s' AND %(where)s" )
        except exc.SQLAlchemyError:
            return None

        if self.transform: return self.transform(val)
        return val

class TrackerSQLMulti( TrackerSQL ):
    '''An SQL tracker spanning multiple databases.

    '''

    databases = ()
    tracks = ()
    
    def __init__(self, *args, **kwargs):
        TrackerSQL.__init__(self, *args, **kwargs )

        if len(self.tracks) == 0:
            raise ValueError("no tracks specified in TrackerSQLMulti")
        if (len(self.tracks) != len(self.databases)):
            raise ValueError("TrackerSQLMulti requires an equal number of tracks (%i) and databases (%i)" \
                                 % (len(self.tracks), len(self.databases)))
        if not self.backend.startswith("sqlite"):
            raise ValueError( "TrackerSQLMulti only works for sqlite database" )

        if not self.db:
            def _my_creator():
                # issuing the ATTACH DATABASE into the sqlalchemy ORM (self.db.execute( ... ))
                # does not work. The database is attached, but tables are not accessible in later
                # SELECT statements.
                import sqlite3
                conn = sqlite3.connect(re.sub( "sqlite:///", "", self.backend) )
                for track, name in zip( self.databases, self.tracks ):
                    conn.execute( "ATTACH DATABASE '%s/csvdb' AS %s" % \
                                      (os.path.abspath(track),
                                       name))
                return conn

            self.connect( creator = _my_creator )

