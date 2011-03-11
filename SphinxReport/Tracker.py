from __future__ import with_statement 

import os, sys, re, types, copy, warnings, ConfigParser, inspect

import sqlalchemy
import sqlalchemy.exceptions

from odict import OrderedDict as odict

# for sqldatabase
if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )

execfile( "conf.py" )

class SQLError( Exception ):
    pass

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

    tracks = []
    slices = []

    def __init__(self):
        pass

    def getTracks( self, subset = None ):
        """return a list of all tracks that this tracker provides."""
        if subset: return subset
        return self.tracks

    def getSlices(self, subset = None):
        """return a list of all slices that this tracker provides.

        The optional subset argument can group slices together.
        """
        return self.slices

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

def getCallerLocals( level = 3, decorators = 0):
    '''returns locals of caller using frame.

    optional pass number of decorators
    
    from http://pylab.blogspot.com/2009/02/python-accessing-caller-locals-from.html
    '''
    f = sys._getframe(level+decorators)
    args = inspect.getargvalues(f)
    return args[3]
    
class TrackerSQL( Tracker ):
    """Base class for trackers that fetch data from an SQL database.
    
    The basic tracker identifies tracks as tables that match a
    certain pattern (:attr:`mPattern`)

    This tracker connects to the database. Each tracker will establish
    its own connection for multi-processing.

    If :attr:`mAsTable` is set, the returned tracks correspond to
    tables.

    """
    mPattern = ""
    mAsTables = False

    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )
        self.db = None

    def __connect( self ):
        """lazy connection function."""

        if not self.db:
            db = sqlalchemy.create_engine( sphinxreport_sql_backend )

            if not db:
                raise ValueError( "could not connect to database %s" % sphinxreport_sql_backend)

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
        """return a list of table objects matching a :term:`track` pattern.

        Note that this function does not return views.
        """
        # old version of sqlalchemy have no sorted_tables attribute
        self.__connect()
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
        '''return a list of tablenames.'''
        return [x.name for x in self.getTables( pattern ) ]

    def hasTable( self, name ):
        """return table with name *name*."""
        self.__connect()
        return name in set( [x.name for x in self.metadata.sorted_tables])

    def getTable( self, name ):
        """return table with name *name*."""
        self.__connect()
        try:
            for table in self.metadata.sorted_tables:
                if table.name == name: return table
        except AttributeError, msg:
            return self.metadata.tables[name]

        raise IndexError( "table %s no found" % name )

    def getColumns( self, name ):
        '''return a list of column names.'''
        c = self.getTable( name ).columns
        return [ re.sub( "%s[.]" % name, "", x.name) for x in c ]

    def execute(self, stmt ):
        self.__connect()
        try:
            r = self.db.execute(stmt)
        except sqlalchemy.exceptions.SQLError, msg:
            raise SQLError(msg)
        return r

    def buildStatement( self, stmt ):
        '''fill in placeholders in stmt.'''
        
        kwargs = self.members( getCallerLocals() )
        statement = stmt % dict( kwargs.items() )
        return statement

    def getValue( self, stmt ):
        """return a single value from an SQL statement.

        This function will return the first value in the first row
        from an SELECT statement.
        """
        return self.execute(self.buildStatement(stmt)).fetchone()[0]

    def getFirstRow( self, stmt ):
        """return a row of values from an SQL statement.

        This function will return the first row
        from an SELECT statement.
        """
        e = self.execute(self.buildStatement(stmt)).fetchone()
        if e: return list(e)
        else: return None

    def getRow( self, stmt ):
        """return a row of values from an SQL statement.

        This function will return the first row
        from an SELECT statement as a dictionary
        of column-value mappings.

        Returns None if result is empty.
        """
        e = self.execute( self.buildStatement( stmt )).fetchone()
        # assumes that values are sorted in ResultProxy.keys()
        if e: return odict( [x,e[x]] for x in e.keys() )
        else: return None

    def getValues( self, stmt ):
        """return all results from an SQL statement.

        This function will return the first value in each row
        from an SELECT statement.
        """
        return [x[0] for x in self.execute(self.buildStatement(stmt)).fetchall() ]

    def getAll( self, stmt ):
        """return all results from an SQL statement.
        """
        # convert to tuples
        e = self.execute(self.buildStatement(stmt))
        columns = e.keys()
        d = e.fetchall()
        return odict( zip( columns, zip( *d ) ) )

    def get( self, stmt ):
        """
        return results from an SQL statement as list of tuples.
        """
        return self.execute(self.buildStatement(stmt)).fetchall()

    def getDict( self, stmt ):
        """return all results from an SQL statement.

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
        """return an iterator of SQL results."""
        return self.execute(stmt)
    
    @property
    def tracks(self):
        """return a list of all tracks that this tracker provides.

        The tracks are defined as tables matching the attribute :attr:`mPattern`.
        """
        rx = re.compile(self.mPattern)
        if self.mAsTables:
            return sorted([ x.name for x in self.getTables() if rx.search( x.name ) ])
        else: 
            result = []
            for x in self.getTables():
                if rx.search(x.name):
                    n = rx.sub( "", x.name )
                    if n == "": n = x.name
                    result.append( n )
            return result

class TrackerSQLCheckTables(TrackerSQL):
    """Tracker that examines the presence/absence of a certain
    field in a list of tables.

    Define the following attributes:

    :attr:`mFields` fields to join
    :attr:`mExcludePattern`: tables to exclude
    :attr:`mPattern`: pattern to define tracks (see :class:`TrackerSql`)
    """

    mFields = ["id",]
    mExcludePattern = None
    mPattern = "_annotations$"
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
        
class TrackerSQLCheckTable(TrackerSQL):
    """Tracker that counts existing entries in a table.

    Define the following attributes:
    :attr:`mExcludePattern`: columns to exclude
    :attr:`mPattern`: pattern to define tracks (see :class:`TrackerSql`)
    """

    mExcludePattern = None
    mPattern = "_evol$"
    
    def __init__(self, *args, **kwargs ):
        TrackerSQL.__init__(self, *args, **kwargs )

    def __call__(self, track, slice = None):
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

class Config( Tracker ):
    '''tracker providing config values.'''

    def __init__(self, *args, **kwargs ):
        Tracker.__init__(self, *args, **kwargs )

    def __call__(self, track, slice = None):
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
        
class Empty( Tracker ):
    '''empty tracker - placeholder for plots that require no input from a tracker.'''

    def getTracks( self, subset = None ):
        """return a list of all tracks that this tracker provides."""
        if subset: return subset
        return ["empty"]

    def __call__(self, track, slice = None ):
        return odict( (("a", 1),))

def prettyFloat( val, format = "%5.2f" ):
    """output a float or "na" if not defined"""
    try:
        x = format % val
    except (ValueError, TypeError):
        x = "na"
    return x
    
def prettyPercent( numerator, denominator, format = "%5.2f" ):
    """output a percent value or "na" if not defined"""
    try:
        x = format % (100.0 * numerator / denominator )
    except (ValueError, ZeroDivisionError):
        x = "na"
    return x
