""" Logging for SphinxReport

Inherited and modified from Leo Goodstadt's ruffus.
"""

import multiprocessing
import multiprocessing.managers

import logging
import logging.handlers

from logging import DEBUG, WARN, INFO

import sys, collections

class CountedLogger:
    """
    Counter that keeps track about how often a logger
    has been called.
    """
    def __init__(self, logger, *args, **kwargs):
        self.mCounts = collections.defaultdict( int )
        self.mLogger = logger

    def debug( self, message ):
        self.mCounts[ 'debug' ] += 1
        return self.mLogger.debug( message )

    def info( self, message ):
        self.mCounts[ 'info' ] += 1
        return self.mLogger.debug( message )

    def warn( self, message ):
        self.mCounts[ 'warn' ] += 1
        return self.mLogger.debug( message )

    def log( self, level, message ):
        self.mCounts[ 'log' ] += 1
        return self.mLogger.log( level, message )

    def getCounts( self ):
        return self.mCounts

#
#   setup_logger 
#
def setup_shared_logger(logging_level, 
                        log_filename, 
                        format = '%(asctime)s %(levelname)s %(message)s' ):
    """
    Function to setup logger shared between all processes
    The logger object will be created within a separate (special) process 
        run by multiprocessing.BaseManager.start()

    See "LoggingManager" below
    """
    print "setting up logger"
    #
    #   Log file name with logger level
    # 
    my_logger = logging.getLogger('My_Pypeline_logger')
    my_logger.setLevel(logging_level)
    print "setting up logger"
    # 
    #   Add handler to print to file, with the specified format  
    #
    handler = logging.handlers.RotatingFileHandler(
        log_filename, 
        maxBytes=100000, 
        backupCount=5)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    
    #
    #   This log object will be wrapped in proxy 
    #
    print "set up logger"
    return CountedLogger(my_logger)

#
#
class LoggerProxy(multiprocessing.managers.BaseProxy):
    """Proxy object for logging

    Logging messages will be marshalled (forwarded) to the
    process where the shared log lives.

    The Proxy object keeps track of the number of times
    debug, log, etc. has been called.
    """

    def debug(self, message):
        return self._callmethod('debug', [message])

    def info(self, message):
        return self._callmethod('info', [message])

    def warn(self, message):
        return self._callmethod('warn', [message])

    def log(self, level,message):
        return self._callmethod('log', [level,message])

    def getCounts(self):
        return self._callmethod('getCounts' )

# 
#   Register the setup_logger function as a proxy for setup_logger
#   
#   We use SyncManager as a base class so we can get a lock proxy for synchronising 
#       logging later on
#
class LoggingManager(multiprocessing.managers.SyncManager):
    """
    Logging manager sets up its own process and will create the real Log object there
    We refer to this (real) log via proxies
    """
    pass

LoggingManager.register('setup_logger', 
                        setup_shared_logger, 
                        proxytype=LoggerProxy, 
                        exposed = ('info', 'debug', 'warn', 'log', 'getCounts' ))
#
#   task function 
#
def pool_do_logging (args):
    logger_proxy, logging_mutex, msg = args
    #
    # make sure logging does not occur at the same time in different processes

    logger_proxy.debug(msg + ", process name = %s" % multiprocessing.current_process().name)
    logger_proxy.info(msg)
    logging_mutex.release()

root = None
logging_mutex = None

def basicConfig( **kwargs ):
    global root
    global logging_mutex

    print "imported"
    if not root:
        print "setting"
        manager = LoggingManager()
        manager.register('setup_logger', 
                         setup_shared_logger,
                         proxytype = LoggerProxy, 
                         exposed = ('info', 'debug', 'warn', 'log', 'getCounts' ))

        print "starting manager"
        manager.start()
        print "started manager"
        filename  = kwargs.get("filename")
        level = kwargs.get("level")
        basic_format = kwargs.get("format", logging.BASIC_FORMAT )

        print "adding logger"
        root = manager.setup_logger(level, filename, basic_format)
        print "adding lock"
        logging_mutex = manager.Lock()

        print "setup finished manager"

def warn(msg, *args, **kwargs):
    """
    Log a message with severity 'WARNING' on the root logger.
    """
    if not root: basicConfig()
    logging_mutex.acquire()
    apply(root.warn, ( ("%s: " % multiprocessing.current_process().name + msg),)+args, kwargs)
    logging_mutex.release()

def debug(msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger.
    """
    if not root: basicConfig()
    logging_mutex.acquire()
    apply(root.debug, ( ("%s: " % multiprocessing.current_process().name + msg),)+args, kwargs)
    logging_mutex.release()

def info(msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger.
    """
    if not root: basicConfig()
    logging_mutex.acquire()
    apply(root.info, ( ("%s: " % multiprocessing.current_process().name + msg),)+args, kwargs)
    logging_mutex.release()

def log(level, msg, *args, **kwargs):
    """
    Log a message with severity 'DEBUG' on the root logger.
    """
    if not root: basicConfig()
    logging_mutex.acquire()
    apply(root.log, ( (level, "%s: " % multiprocessing.current_process().name + msg),)+args, kwargs)
    logging_mutex.release()

def getCounts():
    """
    Log a message with severity 'DEBUG' on the root logger.
    """
    if not root: basicConfig()
    return root.getCounts()

def main( args = sys.argv ):
    
    #
    #   make shared log and proxy 
    #
    manager = LoggingManager()
    manager.register('setup_logger', 
                     setup_shared_logger,
                     proxytype=LoggerProxy, 
                     exposed = ('info', 'debug', 'warn', 'getCounts' ))

    manager.start()
    LOG_FILENAME  = 'ruffus.log'
    LOGGING_LEVEL = logging.DEBUG
    loggerproxy = manager.setup_logger(LOGGING_LEVEL, LOG_FILENAME)
    
    #
    #   make sure we are not logging at the same time in different processes
    #

    
    #
    #   call from main process to make sure works
    # 
    pool_do_logging((loggerproxy, logging_mutex, "help2"))

    #
    #   call from child processes in pool
    # 
    pool = multiprocessing.Pool(processes=4)              # start 4 worker processes
    function_parameters = list()
    for a  in range(200):
        function_parameters.append((loggerproxy, logging_mutex, "message #%3d" % a))
    pool.map(pool_do_logging, function_parameters)
    
    print loggerproxy.getCounts()

if __name__ == '__main__':

    basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        filename = "sphinxreport.log" )

    #
    #   call from main process to make sure works
    # 
    pool_do_logging((root, logging_mutex, "help2"))

    root.warn( "problem" )
    warn( "problem2" )

    #
    #   call from child processes in pool
    # 
    pool = multiprocessing.Pool(processes=4)              # start 4 worker processes
    function_parameters = list()
    for a  in range(200):
        function_parameters.append((root, logging_mutex, "message #%3d" % a))
    pool.map(pool_do_logging, function_parameters)
    
    print root.getCounts()


    #     sys.exit( main( sys.argv) )
