from __future__ import with_statement 

import os, sys, re, types, copy, warnings, ConfigParser, inspect, logging, glob

import sqlalchemy
import sqlalchemy.exc as exc

from SphinxReport import Utils

from odict import OrderedDict as odict

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

        Convenience function for string substitution. If locals is given (and a dictionary),
        the dictionary is added to the returned dictionary.

        Typical usage is::

           print "my string with %(vars)s" % (self.members(locals())).

        returns a dictionary
        '''
        # skip tracks and slices to avoid recursion
        # todo: do this for the general case
        # 1. subtract property attributes, or
        # 2. subtract members of Tracker()
        l = dict( [(attr,getattr(self,attr)) for attr in dir(self) \
                      if not callable(attr) and not attr.startswith("__") and attr != "tracks" and attr != "slices"] )
            
        if locals: return dict( l, **locals)
        else: return l

###########################################################################
###########################################################################
###########################################################################
class TrackerCSV( Tracker ):
    """Base class for trackers that fetch data from an CSV file.
    
    """
    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )
        try: self.filename = kwargs["filename"]
        except KeyError: pass

    def getTracks(self, subset = None ):
        return ["all",]
    
    def getSlices(self, subset = None ):
        return []

    def __call__(self, track, slice = None):
        """return a data structure for track :param: track and slice :slice:"""
        raise NotImplementedError("not implemented")

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

    This tracker connects to the database. Each tracker will establish
    its own connection for efficient multi-processing.

    If :attr:`as_tables` is set, the full table names will be returned.
    The default is to apply :attr:`pattern` and return the result.
    """

    pattern = None
    as_tables = False

    def __init__(self, backend = None, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )

        self.db = None

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
                db = sqlalchemy.create_engine( self.backend, echo = False,
                                               creator = creator )
            else:
                db = sqlalchemy.create_engine( self.backend, echo = False )
            
            if not db:
                raise ValueError( "could not connect to database %s" % self.backend )

            db.echo = False  

            # ignore unknown type BigInt warnings
            if db:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        self.metadata = sqlalchemy.MetaData(db, reflect = True)
                except AttributeError:
                    self.metadata = sqlalchemy.MetaData(db, reflect = True)

            self.db = db

    def getTables(self, pattern = None ):
        """return a list of tables matching a *pattern*.

        This function does not return table views.

        returns a list of table objects.
        """
        # older versions of sqlalchemy have no sorted_tables attribute
        self.connect()
        try:
            sorted_tables = self.metadata.sorted_tables
        except AttributeError, msg:
            sorted_tables = []
            for x in sorted(self.metadata.tables.keys()):
                sorted_tables.append( self.metadata.tables[x])

        if pattern:
            rx = re.compile(pattern)
            return [ x for x in sorted_tables if rx.search( x.name ) ]
        else:
            return sorted_tables

    def getTableNames( self, pattern = None ):
        '''return a list of tablenames matching a *pattern*.
        '''
        return [x.name for x in self.getTables( pattern ) ]

    def hasTable( self, tablename ):
        """return table with name *tablename*."""
        self.connect()
        return tablename in set( [x.name for x in self.metadata.sorted_tables])

    def getTable( self, tablename ):
        """return table or view with name *tablename*."""
        self.connect()
        try:
            for table in self.metadata.sorted_tables:
                if table.name == tablename: return table
        except AttributeError, msg:
            return self.metadata.tables[tablename]

        raise IndexError( "table %s not found" % tablename )

    def getColumns( self, tablename ):
        '''return a list of columns in table *tablename*.'''
        c = self.getTable( tablename ).columns
        return [ re.sub( "%s[.]" % tablename, "", x.name) for x in c ]

    def execute(self, stmt ):
        self.connect()
        try:
            r = self.db.execute(stmt)
        except exc.SQLAlchemyError, msg:
            raise SQLError(msg)
        return r

    def buildStatement( self, stmt ):
        '''fill in placeholders in stmt.'''
        
        kwargs = self.members( getCallerLocals() )
        statement = stmt % dict( kwargs.items() )
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
        if e: return odict( [x,e[x]] for x in e.keys() )
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
        columns = e.keys()
        d = e.fetchall()
        return odict( zip( columns, zip( *d ) ) )

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
        columns = e.keys()
        result = odict()
        for row in e:
            result[row[0]] = odict( zip( columns[1:], row[1:] ) )
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
                return sorted([ x.name for x in tables ] )
            else: 
                return sorted([rx.search( x.name).groups()[0] for x in tables] )
        else:
            return "all"

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
    pattern = "_evol$"
    
    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    def __call__(self, track, *args ):
        """count number of entries in a table."""

        statement = "SELECT COUNT( %s) FROM %s WHERE %s IS NOT NULL" 

        table = self.getTable( track + "_evol" )
        data = []

        if self.mExcludePattern: 
            fskip = lambda x: re.search( self.mExcludePattern, x )
        else:
            fskip = lambda x: False
            
        for column in [x.name for x in table.columns]:
            if fskip( column ): continue
            data.append( (column, self.getValue( statement % (column, table.name, column) ) ) )
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

        config = ConfigParser.ConfigParser()
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
                x[key] = odict( zip( ("value", "type" ), convert( value )) )
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

    The tracks are given by rows in table :attribute:`table`. The tracks are
    specified by the :attribute:`fields`. 

    :attribute:`fields` is a tuple of column names (default = ``(track,)``).

    If multiple columns are specified, they will all be used to define the 
    tracks in the table.

    Rows in the table need to be unique for any combination :attribute:`fields`.

    attribute:`extra_columns` can be used to add additional columns to the table.
    This attribute is a dictionary.
    '''
    exclude_columns = ()
    table = None
    fields = ("track",)
    extra_columns = {}
    sort = None

    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    @property
    def tracks( self ):
        if not self.hasTable( self.table ): return []
        if self.sort: sort = "ORDER BY %s" % self.sort
        else: sort = ""
        d = self.get( "SELECT DISTINCT %s FROM %s %s" % (",".join(self.fields), self.table, sort ))
        if len(self.fields) == 1:
            return tuple( [x[0] for x in d ] )
        else:
            return tuple( [tuple(x) for x in d ] )

    @property
    def slices( self ):
        columns = self.getColumns( self.table ) 
        return [ x for x in columns if x not in self.exclude_columns and x not in self.fields ] + self.extra_columns.keys()

    def __call__(self, track, slice = None ):
        if len(self.fields) == 1: track = (track,)
        wheres = " AND ".join([ "%s = '%s'" % (x,y) for x,y in zip( self.fields, track ) ] )
        if slice in self.extra_columns: 
            slice = "%s AS %s" % (self.extra_columns[slice], slice)
        return self.getValue( "SELECT %(slice)s FROM %(table)s WHERE %(wheres)s" ) 

###########################################################################
###########################################################################
###########################################################################

class SingleTableTrackerColumns( TrackerSQL ):
    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by :attribute:`column` and one for a track.

    The tracks are derived from all columns in table :attribute:`table`. By default,
    all columns are taken as tracks apart from :attribute:`column` and those
    listed in :attribute:`exclude_columns`.

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
        return self.getValues( "SELECT DISTINCT %(column)s FROM %(table)s" )

    def __call__(self, track, slice = None ):
        data = self.getValue( "SELECT %(track)s FROM %(table)s WHERE %(column)s = '%(slice)s'" )
        return data

###########################################################################
###########################################################################
###########################################################################

class SingleTableTrackerHistogram( TrackerSQL ): 
    '''Tracker representing a table with multiple tracks.

    Returns a dictionary of two sets of data, one given
    by :attribute:`column` and one for a track.

    The tracks are derived from all columns in table :attribute:`table`. By default,
    all columns are taken as tracks apart from :attribute:`column` and those
    listed in :attribute:`exclude_columns`.

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

###########################################################################
###########################################################################
###########################################################################
class SingleTableTrackerEdgeList( TrackerSQL ):
    '''Tracker representing a table with matrix type data.

    Returns a dictionary of values.

    The tracks are given by entries in the :attribute:`row` column in a table :attribute:`table`. 
    The slices are given by entries in the :attribute:`column` column in a table.

    The :attribute:`fields` is a third column specifying the value returned. If :attribute:`where`
    is set, it is added to the SQL statement to permit some filtering.

    If :attribute:`transform` is set, it is applied to the value.

    This method is inefficient, particularly so if there are no indices on :attribute:`row` and :attribute:`column`.

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
