import re, os, sys, imp, cStringIO, types
import traceback
import ConfigParser

import SphinxReport
from SphinxReport.Tracker import Tracker
from SphinxReport.ResultBlock import ResultBlocks,ResultBlock
from SphinxReport.Component import *

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

PARAMS = {}

def convertValue( value, list_detection = False ):
    '''convert a value to int, float or str.'''
    rx_int = re.compile("^\s*[+-]*[0-9]+\s*$")
    rx_float = re.compile("^\s*[+-]*[0-9.]+[.+\-eE][+-]*[0-9.]*\s*$")

    if value == None: return value

    if list_detection and "," in value:
        values = []
        for value in value.split(","):
            if rx_int.match( value ):
                values.append( int(value) )
            elif rx_float.match( value ):
                values.append( float(value) )
            else:
                values.append(value)
        return values
    else:
        if rx_int.match( value ):
            return int(value)
        elif rx_float.match( value ):
            return float(value)
        return value

def configToDictionary( config ):

    p = {}
    for section in config.sections():
        for key,value in config.items( section ):
            v = convertValue( value )
            p["%s_%s" % (section,key)] = v
            if section == "general":
                p["%s" % (key)] = v
               
    for key, value in config.defaults().iteritems():
        p["%s" % (key)] =  convertValue( value )
        
    return p

def getParameters( filenames = ["sphinxreport.ini",] ):
    '''read a config file and return as a dictionary.

    Sections and keys are combined with an underscore. If
    a key without section does not exist, it will be added 
    plain.

    For example::

       [general]
       input=input1.file

       [special]
       input=input2.file

    will be entered as { 'general_input' : "input1.file",
    'input: "input1.file", 'special_input' : "input2.file" }

    This function also updates the module-wide parameter map.
    
    The section [DEFAULT] is equivalent to [general].
    '''

    global CONFIG

    CONFIG = ConfigParser.ConfigParser()
    CONFIG.read( filenames )

    p = configToDictionary( CONFIG )
    PARAMS.update( p )

    return PARAMS

getParameters( filenames = ["sphinxreport.ini",] )

## read placeholders from config file in current directory
## It would be nice to read default values, but the location 
## of the documentation source files are not known to this module. 

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
        except ImportError, msg:
            warn("could not find module %s: msg=%s" % (name,msg) )        
            raise ImportError("could not find module %s: msg=%s" % (name,msg) )

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

def isClass( obj ):
    '''return true if obj is a class.
    
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

def makeObject( path, *args, **kwargs ):
    '''return object of type *path*

    This function is similar to an import statement, but
    also instantiates the class and returns the object.

    The object is instantiated with *args* and **kwargs**.
    '''

    # split class from module
    name, cls = os.path.splitext(path)

    # remove leading '.'
    cls = cls[1:]

    debug( "instantiating class %s" % cls )

    module, pathname = getModule( name )

    # get class from module
    obj = getattr( module, cls)

    # instantiate, if it is a class
    if isClass( obj ):
        try:
            obj = obj( *args, **kwargs )
        except AttributeError, msg:
            critical( "instantiating class %s.%s failed: %s" % (module, cls, msg))
            raise
        
    return obj, module, pathname, cls
    
@memoized
def makeTracker( path, *args, **kwargs ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """

    obj, module, pathname, cls = makeObject( path, *args, **kwargs )
    code = getCode( cls, pathname )
    return code, obj

@memoized
def makeRenderer( path, *args, **kwargs ):
    """retrieve an instantiated Renderer.
    
    returns the object.
    """
    obj, module, pathname, cls = makeObject( path, *args, **kwargs )
    return obj

@memoized
def makeTransformer( path, *args, **kwargs ):
    """retrieve an instantiated Transformer.
    
    returns the object.
    """
    obj, module, pathname, cls = makeObject( path, *args, **kwargs )
    return obj


def buildException( stage ):
    '''build an exception text element.
    
    It uses the last exception.
    '''
        
    if sphinxreport_show_errors:
        EXCEPTION_TEMPLATE = '''
.. error:: %(exception_name)s

   * stage: %(stage)s
   * exception: %(exception_name)s
   * message: %(exception_value)s
   * traceback: 

%(exception_stack)s
'''

        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        lines = traceback.format_tb( exceptionTraceback )
        # remove all the ones relate to Dispatcher.py
        xlines = filter( lambda x: not re.search( "Dispatcher.py", x ), lines )
        # if nothing left, use the full traceback
        if len(xlines) > 0: lines = xlines
        # add prefix of 6 spaces
        prefix = "\n" + " " * 6
        exception_stack  = prefix + prefix.join( "".join(lines).split("\n") )
        if exceptionType.__module__ == "exceptions":
            exception_name   = exceptionType.__name__
        else:
            exception_name   = exceptionType.__module__ + '.' + exceptionType.__name__

        exception_value  = str(exceptionValue)

        return ResultBlocks( 
            ResultBlocks( 
                ResultBlock( EXCEPTION_TEMPLATE % locals(), 
                         title = "" ) ) )
    else:
        return ResultBlocks()


def getTransformers( transformers, **kwargs ):
    '''find and instantiate all transformers.'''

    result = []
    for transformer in transformers:
        k = "transform-%s" % transformer
        if k in getPlugins()["transform"]:
            cls = getPlugins()["transform"][k]
            instance = cls( **kwargs)
        else:
            instance = makeTransformer( transformer )

        if not instance:
            msg = "could not find transformer '%s'. Available transformers:\n  %s" % \
                (transformer, "\n  ".join(sorted(getPlugins()["transform"].keys())))
            raise KeyError( msg )

        result.append( instance )

    return result

def updateOptions( kwargs ):
    '''replace placeholders in kwargs with
    with PARAMS read from config file.
    
    returns the update dictionary.
    '''

    for key, value in kwargs.items():
        try:
            v = value.strip()
        except AttributeError:
            # ignore non-string types
            continue
            
        if v.startswith("@") and v.endswith("@"):
            code = v[1:-1]
            if code in PARAMS:
                kwargs[key] = PARAMS[code]
            else:
                raise ValueError("unknown placeholder `%s`" % code )

    return kwargs

def getRenderer( renderer_name, **kwargs ):
    '''find and instantiate renderer.'''

    try:
        cls = getPlugins()["render"]["render-%s" % renderer_name]
        renderer = cls( **kwargs )
    except KeyError:
        renderer = makeRenderer( renderer_name, **kwargs)

    if not renderer:
        raise KeyError( "could not find renderer '%s'. Available renderers:\n  %s" % \
                            (renderer_name, 
                             "\n  ".join(sorted(getPlugins()["render"].keys()))))

    return renderer

