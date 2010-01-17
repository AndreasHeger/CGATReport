from __future__ import with_statement 

import os, sys, re, types, copy, warnings, ConfigParser

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

    mXLabel = None
    mYLabel = None

    def __init__(self):
        pass

    def getTracks( self, subset = None ):
        """return a list of all tracks that this tracker provides."""
        if subset: return subset
        return []

    def getSlices(self, subset = None):
        """return a list of all slices that this tracker provides.

        The optional subset argument can group slices together.
        """
        return []

    def getXLabel(self): 
        """return the default xlabel."""
        return self.mXLabel

    def getYLabel(self): 
        """return the default ylabel."""
        return self.mYLabel

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
        raise NotImplementedError("not implemented")

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
            db = sqlalchemy.create_engine( sql_backend )

            if not db:
                raise ValueError( "could not connect to database %s" % sql_backend)

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
        """return a list of table objects matching a :term:`track` pattern."""
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

    def getValue( self, stmt ):
        """return a single value from an SQL statement.

        This function will return the first value in the first row
        from an SELECT statement.
        """
        return self.execute(stmt).fetchone()[0]

    def getFirstRow( self, stmt ):
        """return a row of values from an SQL statement.

        This function will return the first row
        from an SELECT statement.
        """
        return list(self.execute(stmt).fetchone())

    def getValues( self, stmt ):
        """return all results from an SQL statement.

        This function will return the first value in each row
        from an SELECT statement.
        """
        return [x[0] for x in self.execute(stmt).fetchall() ]

    def getAll( self, stmt ):
        """return all results from an SQL statement.
        """
        # convert to tuples
        return [ tuple(x) for x in self.execute(stmt).fetchall() ]

    def getIter( self, stmt ):
        """return an iterator of SQL results."""
        return self.execute(stmt)

    def getTracks( self, subset = None ):
        """return a list of all tracks that this tracker provides.

        The tracks are defined as tables matching the attribute :attr:`mPattern`.
        """
        if subset: return subset
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
        
