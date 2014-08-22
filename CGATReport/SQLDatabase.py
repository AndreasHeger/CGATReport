
import os
import sys

from sqlalchemy import *
from sqlalchemy.ext.sqlsoup import SqlSoup

# ignore unknown type BigInt warnings
try:
    db = create_engine(sql_backend)
    db.echo = False
except NameError:
    db = None

if db:
    pass
    #import warnings
    # with warnings.catch_warnings():
    #    warnings.simplefilter("ignore")
    #    metadata = MetaData(db, reflect = True)


def getTables():
    return metadata.sorted_tables


def getTable(name):
    """return table with name *name*."""
    for table in metadata.sorted_tables:
        if table.name == name:
            return table
    raise IndexError("table %s no found" % name)


def execute(stmt):
    return db.execute(stmt)


def getValue(stmt):
    """return a single value from an SQL statement.

    This function will return the first value in the first row
    from an SELECT statement.
    """
    return execute(stmt).fetchone()[0]


def getValues(stmt):
    """return all results from an SQL statement.

    This function will return the first value in each row
    from an SELECT statement.
    """
    return [x[0] for x in execute(stmt).fetchall()]


def getAll(stmt):
    """return all results from an SQL statement.
    """
    return execute(stmt).fetchall()
