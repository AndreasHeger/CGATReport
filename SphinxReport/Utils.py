import re, os, sys, imp, cStringIO, types, traceback, logging, math

import ConfigParser

import SphinxReport
from SphinxReport.ResultBlock import ResultBlocks,ResultBlock
from SphinxReport.Component import *
import SphinxReport.Config

from SphinxReport.odict import OrderedDict as odict

import types, copy, numpy

ContainerTypes = (types.TupleType, types.ListType, type(numpy.zeros(0)))

# set with keywords that will not be pruned
# This is important for the User Tracker
TrackerKeywords = set( ( "text", "rst", "xls", ) )

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

def asList( param ):
    '''return a param as a list'''
    if type(param) not in (types.ListType, types.TupleType):
        return [x.strip() for x in param.split(",")]
    else: return param

def quote_rst( text ):
    '''quote text for restructured text.'''
    return re.sub( r"([*])", r"\\\1", str(text))

def quote_filename( text ):
    '''quote filename for use as link in restructured text (remove spaces, etc).'''
    return re.sub( r"""[ '"()\[\]]""", r"_", str(text))

# default values
PARAMS = {
    "report_show_errors" : True,
    "report_show_warnings" : True,
    "report_sql_backend" : "sqlite:///./csvdb",
    "report_cachedir" : "_cache",
    "report_urls" : "data,code,rst",
    "report_images" : "hires,hires.png,200,eps,eps,50",
    }

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

def selectAndDeleteOptions( options, select ):
    '''collect options in *select* and from *options* and remove those found.

    returns dictionary of options found.
    '''
    new_options = {}
    for k, v in options.items():
        if k in select:
            new_options[k] = v
            del options[k]
    return new_options

def getImageFormats( display_options = None ):
    '''return list of image formats to render (in addition to the default format).'''

    def _toFormat( format ):
        if len(data) == 1:
            return (data[0], data[0], 100 ) 
        elif len(data) == 2:
            return (data[0], data[1], 100 )
        elif len(data) == 3:
            return (data[0], data[1], int(data[2]) )
        else: raise ValueError( ":format: option expects one to three params, not %s" % data)

    if "display" in display_options:
        all_data = [ x.strip() for x in display_options["display"].split(";")]
        if len(all_data) > 1: 
            warn(":display: only expects one format, additional ignored at %s" % display_options["display"])
        data = asList( all_data[0] )
        default_format = _toFormat( data )
    else:
        default_format = SphinxReport.Config.HTML_IMAGE_FORMAT

    # get default extra formats from the config file
    additional_formats = []
    if "report_images" in PARAMS:
        data = asList( PARAMS["report_images"] )
        if len(data) % 3 != 0: raise ValueError( "need multiple of 3 number of arguments to report_images option" )
        for x in xrange( 0, len(data), 3 ):
            additional_formats.append( (data[x], data[x+1], int(data[x+2]) ) )
    else:
            additional_formats.extend( SphinxReport.Config.ADDITIONAL_FORMATS )

    # add formats specified in the document
    if "extra-formats" in display_options:
        all_data = [ x.strip() for x in display_options["extra-formats"].split(";")]
        for data in all_data:
            data = asList( all_data[0] )
            additional_formats.append( _toFormat( data ) )

    if SphinxReport.Config.LATEX_IMAGE_FORMAT: additional_formats.append( SphinxReport.Config.LATEX_IMAGE_FORMAT )
        
    return default_format, additional_formats

def getImageOptions( display_options = None):
    '''return string with display_options for ``:image:`` directive.'''
    if display_options:
        return "\n".join( \
            ['      :%s: %s' % (key, val) for key, val in display_options.iteritems() \
                 if key not in ('format', 'extra-formats')] )
    else:
        return ''

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
   def __call__(self, *args ):
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
    logging.debug( "entered getModule with `%s`" % name )

    parts = name.split(".")
    if parts[0] == "Tracker":
        # special case: Trackers shipped with SphinxReport
        if len(parts) > 2:
            raise NotImplementedError( "built-in trackers are Tracker.<name> " )
        name = "Tracker" 
        path = [ os.path.join( SphinxReport.__path__[0] ) ]

    # the first part needs to be on the python sys.path
    elif len(parts) > 1:
        try:
            (file, pathname, description ) = imp.find_module( parts[0] )
        except ImportError, msg:
            warn("could not find module %s: msg=%s" % (name,msg) )        
            raise ImportError("could not find module %s: msg=%s" % (name,msg) )

        path = [ os.path.join( pathname, *parts[1:-1] ) ]
        name = parts[-1]
    else:
        path = None

    debug( "searching for module name=%s at path=%s" % (name, str(path)))

    # find module
    try:
        (modulefile, pathname, description) = imp.find_module( name, path )
    except ImportError, msg:
        warn("could not find module %s: msg=%s" % (name,msg) )        
        raise ImportError("could not find module %s: msg=%s" % (name,msg) )

    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    debug( "loading module: %s: %s, %s, %s" % (name, modulefile, pathname, description) )
    # imp.load_module modifies sys.path - save original and restore
    oldpath = sys.path

    # add to sys.path to ensure that imports in the directory work
    if pathname not in sys.path:
        sys.path.append( os.path.dirname( pathname ) )

    try:
        module = imp.load_module(name, modulefile, pathname, description )
    except:
        warn("could not load module %s" % name )        
        raise
    finally:
        modulefile.close()
        sys.stdout = stdout
        sys.path = oldpath

    return module, pathname

def getCode( cls, pathname ):
    '''retrieve code for methods and functions.'''
    # extract code
    code = []
    infile = open( pathname, "r")
    for line in infile:
        x = re.search( "(\s*)(class|def)\s+%s" % cls, line ) 
        if x:
            indent = len( x.groups()[0] )
            code.append( line )
            break
    for line in infile:
        if len( re.match( "^(\s*)", line).groups()[0] ) <= indent: break
        code.append(line)
    infile.close()

    return code

def indent( text, indent ):
    '''return *text( indented by *indent*.'''

    return "\n".join( [ " " * indent + x for x in text.split("\n") ] )

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

def makeObject( path, args = (), kwargs = {} ):
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
    try:
        obj = getattr( module, cls)
    except AttributeError:
        raise AttributeError( "%s has no attribute '%s'" % (module, pathname, cls) )
    # instantiate, if it is a class
    if isClass( obj ):
        try:
            obj = obj( *args, **kwargs )
        except AttributeError, msg:
            critical( "instantiating class %s.%s failed: %s" % (module, cls, msg))
            raise
        
    return obj, module, pathname, cls
    
@memoized
def makeTracker( path, args = (), kwargs = {} ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """
    obj, module, pathname, cls = makeObject( path, args, kwargs )
    code = getCode( cls, pathname )
    return code, obj

@memoized
def makeRenderer( path, args = (), kwargs = {}):
    """retrieve an instantiated Renderer.
    
    returns the object.
    """
    obj, module, pathname, cls = makeObject( path, args, kwargs )
    return obj

@memoized
def makeTransformer( path, args = (), kwargs = {}):
    """retrieve an instantiated Transformer.
    
    returns the object.
    """
    obj, module, pathname, cls = makeObject( path, args, kwargs )
    return obj


def buildWarning( name, message ):
    '''build a sphinxreport warning message with name *name*
    and message *message*.

    Note that *name* should not contain any spaces.

    '''
    if PARAMS["report_show_warnings"]:
        WARNING_TEMPLATE = '''

.. warning:: %(name)s

   * %(message)s

'''
        name = re.sub("\s", "_", name )
        return ResultBlock( WARNING_TEMPLATE % locals(), 
                            title = "" )
    else:
        return None
        
def buildException( stage ):
    '''build an exception text element.
    
    It uses the last exception.
    '''
        
    if PARAMS["report_show_errors"]:
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
        # xlines = filter( lambda x: not re.search( "Dispatcher.py", x ), lines )
        xlines = lines
        # if nothing left, use the full traceback
        if len(xlines) > 0: lines = xlines
        # add prefix of 6 spaces
        prefix = "\n" + " " * 6
        exception_stack  = quote_rst( prefix + prefix.join( "".join(lines).split("\n") ))
        if exceptionType.__module__ == "exceptions":
            exception_name   = quote_rst(exceptionType.__name__)
        else:
            exception_name   = quote_rst( exceptionType.__module__ + '.' + exceptionType.__name__ )

        exception_value  = quote_rst( str(exceptionValue) )

        return ResultBlock( EXCEPTION_TEMPLATE % locals(), 
                            title = "" )
    else:
        return None

def getTransformers( transformers, kwargs = {} ):
    '''find and instantiate all transformers.'''

    result = []
    for transformer in transformers:
        k = "transform-%s" % transformer
        if k in getPlugins()["transform"]:
            cls = getPlugins()["transform"][k]
            instance = cls( **kwargs)
        else:
            instance = makeTransformer( transformer, (), kwargs )

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

def getRenderer( renderer_name, kwargs = {} ):
    '''find and instantiate renderer.'''

    renderer = None

    try:
        cls = getPlugins()["render"]["render-%s" % renderer_name]
        renderer = cls( **kwargs )
    except KeyError:
        # This was uncommented to fix one bug
        # but uncommenting invalidates user renderers
        # TODO: needs to be revisited
        renderer = makeRenderer( renderer_name, kwargs)

    if not renderer:
        raise KeyError( "could not find renderer '%s'. Available renderers:\n  %s" % \
                            (renderer_name, 
                             "\n  ".join(sorted(getPlugins()["render"].keys()))))

    return renderer

from pkg_resources import resource_string
from pkgutil import get_loader

def my_get_data(package, resource):
    """Get a resource from a package.

    This is a wrapper round the PEP 302 loader get_data API. The package
    argument should be the name of a package, in standard module format
    (foo.bar). The resource argument should be in the form of a relative
    filename, using '/' as the path separator. The parent directory name '..'
    is not allowed, and nor is a rooted name (starting with a '/').

    The function returns a binary string, which is the contents of the
    specified resource.

    For packages located in the filesystem, which have already been imported,
    this is the rough equivalent of

        d = os.path.dirname(sys.modules[package].__file__)
        data = open(os.path.join(d, resource), 'rb').read()

    If the package cannot be located or loaded, or it uses a PEP 302 loader
    which does not support get_data(), then None is returned.
    """

    loader = get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None
    
    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)    
    return loader.get_data(resource_name)

## get_data only available in python >2.6
try:
    from pkgutil import get_data
except ImportError: 
    get_data = my_get_data

def getTemplatesDir():
    '''returns the location of the templates.'''
    return os.path.join( os.path.dirname( __file__), "templates" )

def layoutBlocks( blocks, layout = "column"):
    """layout blocks of rst text.

    layout can be one of "column", "row", or "grid".

    The layout uses an rst table to arrange elements.
    """

    lines = []
    if len(blocks) == 0: return lines

    # flatten blocks
    x = ResultBlocks()
    for b in blocks:
        if b.title: b.updateTitle( b.title, "prefix" )
        try:
            x.extend( b )
        except TypeError:
            x.append( b )

    blocks = x

    if layout == "column":
        for block in blocks: 
            if block.title:
                lines.extend( block.title.split("\n") )
                lines.append( "" )
            else:
                logging.warn( "report_directive.layoutBlocks: missing title" )

            lines.extend(block.text.split("\n"))
        lines.extend( [ "", ] )
        return lines

    elif layout in ("row", "grid"):
        if layout == "row": ncols = len(blocks)
        elif layout == "grid": ncols = int(math.ceil(math.sqrt( len(blocks) )))

    elif layout.startswith("column"):
        ncols = min( len(blocks), int(layout.split("-")[1]))
        # TODO: think about appropriate fix for empty data
        if ncols == 0: 
            ncols = 1
            return lines

    else:
        raise ValueError( "unknown layout %s " % layout )

    # compute column widths
    widths = [ x.getWidth() for x in blocks ]
    text_heights = [ x.getTextHeight() for x in blocks ]
    title_heights = [ x.getTitleHeight() for x in blocks ]

    columnwidths = []
    for x in range(ncols):
        columnwidths.append( max( [widths[y] for y in range( x, len(blocks), ncols ) ] ) )

    separator = "+%s+" % "+".join( ["-" * x for x in columnwidths ] )

    ## add empty blocks
    if len(blocks) % ncols:
        blocks.extend( [ ResultBlock( "", "" )]  * (ncols - len(blocks) % ncols) )

    for nblock in range(0, len(blocks), ncols ):

        ## add text
        lines.append( separator )
        max_height = max( text_heights[nblock:nblock+ncols] )
        new_blocks = ResultBlocks()
        
        for xx in range(nblock, min(nblock+ncols,len(blocks))):
            txt, col = blocks[xx].text.split("\n"), xx % ncols

            max_width = columnwidths[col]

            # add missig lines 
            txt.extend( [""] * (max_height - len(txt)) )
            # extend lines
            txt = [ x + " " * (max_width - len(x)) for x in txt ]

            new_blocks.append( txt )

        for l in zip( *new_blocks ):
            lines.append( "|%s|" % "|".join( l ) )

        ## add subtitles
        max_height = max( title_heights[nblock:nblock+ncols] )

        if max_height > 0:

            new_blocks = ResultBlocks()
            lines.append( separator )

            for xx in range(nblock, min(nblock+ncols,len(blocks))):
                
                txt, col = blocks[xx].title.split("\n"), xx % ncols

                max_width = columnwidths[col]
                # add missig lines 
                txt.extend( [""] * (max_height - len(txt) ) )
                # extend lines
                txt = [ x + " " * (max_width - len(x)) for x in txt ]

                new_blocks.append( txt )

            for l in zip( *new_blocks ):
                lines.append( "|%s|" % "|".join( l ) )

    lines.append( separator )
    lines.append( "" )

    return lines

