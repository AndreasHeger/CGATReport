'''basic module for Sphinxreport actors.
'''

import os, sys
import pkg_resources
from logging import warn, log, debug, info, critical
import logging
import collections
from docutils.parsers.rst import directives

LOGFILE = "sphinxreport.log"
LOGGING_FORMAT='%(asctime)s %(levelname)s %(message)s'

logging.basicConfig(
    level=logging.DEBUG,
    format= LOGGING_FORMAT,
    stream = open( LOGFILE, "a" ) )

class Component(object):
    '''base class for SphinxReport components.
    '''

    # options exported to sphinx
    options = ()

    def __init__(self, *args, **kwargs ):
        pass

    def debug( self, msg ):
        debug( "disp%s: %s" % (id(self),msg) )
    def warn( self, msg ):
        warn( "disp%s: %s" % (id(self),msg) ) 
    def info( self, msg ):
        info( "disp%s: %s" % (id(self),msg) ) 
    def critical( self, msg ):
        critical( "disp%s: %s" % (id(self),msg) ) 

# plugins are only initialized once they are called
# for in order to remove problems with cyclic imports
plugins = None
options = None
ENTRYPOINT = 'SphinxReport.plugins'

def init_plugins():

    info( "initialising plugins" )
    try:
        pkg_resources.working_set.add_entry(sphinxreport_plugins)
        pkg_env = pkg_resources.Environment(sphinxreport_plugins)
    except NameError:
        pkg_env = pkg_resources.Environment()
        
    plugins = collections.defaultdict( dict )
    for name in pkg_env:
        egg = pkg_env[name][0]
        egg.activate()
        modules = []
        for name in egg.get_entry_map(ENTRYPOINT):
            entry_point = egg.get_entry_info(ENTRYPOINT, name)
            cls = entry_point.load()
            if not hasattr(cls, 'capabilities'):
                cls.capabilities = []
                
            for c in cls.capabilities:
                plugins[c][name] = cls
    if len(plugins) == 0:
        warn("did not find any plugins")
    else:
        debug("found plugins: %i capabilites and %i plugins" % \
                  (len(plugins), sum( [len(x) for x in plugins.values() ] ) ))

    return plugins

def getPlugins(capability  = None):
    global plugins
    if not plugins: plugins = init_plugins()
    if capability == None:
        return plugins
        result = set()
        for p in plugins.itervalues():
            for plugin in p:
                result.add(plugin)
        return list(result)
    else:
        return plugins.get(capability, {})


def getOptionMap():
    global options

    if options == None:
        options = {}
        for section, plugins in getPlugins().iteritems():
            options[section] = {}
            for name, cls in plugins.iteritems():
                try:
                    options[section].update( dict( cls.options) )
                except AttributeError:
                    pass
        options["dispatch"] = {
            'groupby': directives.unchanged,
            'tracker': directives.unchanged,
            'tracks': directives.unchanged,
            'slices': directives.unchanged,
            'layout': directives.unchanged,
            'nocache': directives.flag,
            }

        options["display"]  = {
            'alt': directives.unchanged,
            'height': directives.length_or_unitless,
            'width': directives.length_or_percentage_or_unitless,
            'scale': directives.nonnegative_int,
            # 'align': align,
            'class': directives.class_option,
            'render' : directives.unchanged,
            'transform' : directives.unchanged,
            'include-source': directives.flag 
            }

    return options

def getOptionSpec():
    '''build option spec for sphinx
    
    This method returns a flattened :var:`options`.
    '''
    o = getOptionMap()
    r = {}
    for x, xx in o.iteritems(): r.update( xx )
        
    # add the primary actor options
    r["render"] = directives.unchanged
    r["transform"] = directives.unchanged

    return r
