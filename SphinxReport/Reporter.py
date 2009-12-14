'''basic module for Sphinxreport actors.
'''

import os

from logging import warn, log, debug, info
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( "sphinxreport.log", "a" ) )

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
