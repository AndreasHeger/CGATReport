'''basic module for Sphinxreport actors.
'''

import os

LOGFILE = "sphinxreport.log"

from logging import warn, log, debug, info
import logging

LOGGING_FORMAT='%(asctime)s %(levelname)s %(message)s'

logging.basicConfig(
    level=logging.DEBUG,
    format= LOGGING_FORMAT,
    stream = open( LOGFILE, "a" ) )

# read configuration options - variables are imported in
# this namespace.
if not os.path.exists("conf.py"):
    raise IOError( "could not find conf.py" )
execfile( "conf.py" )

class Reporter(object):
    '''base class for SphinxReport actors.

    Implements logging facilities.
    '''
    def __init__(self, *args, **kwargs ):
        pass

    def debug( self, msg ):
        debug( "disp%s: %s" % (id(self),msg) )
    def warn( self, msg ):
        warn( "disp%s: %s" % (id(self),msg) ) 
    def info( self, msg ):
        info( "disp%s: %s" % (id(self),msg) ) 
