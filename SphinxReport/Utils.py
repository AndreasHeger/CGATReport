import re, os, sys, imp, cStringIO, types

import SphinxReport
from SphinxReport.Tracker import Tracker
from SphinxReport.Reporter import *

from SphinxReport.odict import OrderedDict as odict

import types, copy, numpy

ContainerTypes = (types.TupleType, types.ListType, type(numpy.zeros(0)))
# Taken from numpy.scalartype, but removing the types object and unicode
# None is allowed to represent missing values. numpy.float128 is a recent
# numpy addition.
try:
    NumberTypes = (types.IntType, types.FloatType, types.LongType, types.NoneType,
               numpy.int8, numpy.int16, numpy.int32, numpy.int64, 
               numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, 
               numpy.float32, numpy.float64, numpy.float128 )
except AttributeError, msg:
    NumberTypes = (types.IntType, types.FloatType, types.LongType, types.NoneType,
               numpy.int8, numpy.int16, numpy.int32, numpy.int64, 
               numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64, 
               numpy.float32, numpy.float64 )
    

def isArray( data ):
    '''return True if data is an array.'''
    return type(data) in ContainerTypes
    
def is_numeric(obj):
    attrs = ['__add__', '__sub__', '__mul__', '__div__', '__pow__']
    return all(hasattr(obj, attr) for attr in attrs)

def quote_filename( fn ):
    '''quote a filename.
    latex does not permit a "." for image files - replace it with "-"
    '''
    return re.sub( "[.]", "-", fn )

def quote_rst( text ):
    '''quote text for restructured text.'''
    return re.sub( r"([*])", r"\\\1", str(text))

class memoized(object):
   """Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         self.cache[args] = value = self.func(*args)
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring."""
      return self.func.__doc__

@memoized
def getModule( name ):
    """load module in fullpath
    """
    # remove leading '.'
    debug( "entered getModule with `%s`" % name )

    parts = name.split(".")
    # note that find_module is NOT recursive - implement later
    if len(parts) > 1:
        raise NotImplementedError( "hierarchical module names not implemented yet." )

    # find in user specified directories
    if name == "Tracker":
        return SphinxReport.Tracker, os.path.join( SphinxReport.__path__[0], "Tracker.py")
    else:
        try:
            (file, pathname, description) = imp.find_module( name )
        except ImportError:
            warn("could not find module %s" % name )        
            raise ImportError("could not find module %s" % name )

    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    debug( "loading module: %s: %s, %s, %s" % (name, file, pathname, description) )
    
    try:
        module = imp.load_module(name, file, pathname, description )
    except:
        warn("could not load module %s" % name )        
        raise
    finally:
        file.close()
        sys.stdout = stdout

    return module, pathname

def getCode( cls, pathname ):
    '''retrieve code.'''
    # extract code
    code = []
    infile = open( pathname, "r")
    for line in infile:
        x = re.search( "(\s*)class\s+%s" % cls, line ) 
        if x:
            indent = len( x.groups()[0] )
            code.append( line )
            break
    for line in infile:
        if len( re.match( "^(\s*)", line).groups()[0] ) <= indent: break
        code.append(line)
    infile.close()

    return code

def isTracker( obj ):
    '''return true if obj is a valid tracker.
    
    return False if it is a function object.
    raise ValueError if neither
    '''
    
    # checking for subclass of Tracker causes a problem
    # for classes defined in the module Tracker itself.
    # The problem is that 'Tracker' is SphinxReport.Tracker.Tracker,
    # while the one in tracker is simply Tracker
    # issubclass(obj, Tracker) and \
    
    if isinstance(obj, (type, types.ClassType)) and \
            hasattr(obj, "__call__"):
        return True
    elif isinstance(obj, (type, types.FunctionType)):
        return False
    elif isinstance(obj, (type, types.LambdaType)):
        return False
    
    raise ValueError("can not make sense of tracker %s" % str(obj))

@memoized
def getTracker( fullpath ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """
    name, cls = os.path.splitext(fullpath)
    # remove leading '.'
    cls = cls[1:]

    module, pathname = getModule( name )

    code = getCode( cls, pathname )

    debug( "instantiating tracker %s" % cls )

    # get tracker
    obj = getattr( module, cls)

    # instantiate, if it is a tracker
    if isTracker( obj ):
        try:
            obj = obj()
        except AttributeError, msg:
            critical( "instantiating tracker %s.%s failed: %s" % (module, cls, msg))
            raise
        
    return code, obj

