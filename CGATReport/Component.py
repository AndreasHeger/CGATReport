'''basic module for CGATReport actors.
'''
from __future__ import unicode_literals

import logging
import sys
import traceback

from CGATReport.Types import force_encode, get_encoding

LOGFILE = "cgatreport.log"
LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'


def get_logger():

    logger = logging.getLogger(
        "cgatreport")

    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        fh = logging.FileHandler(
            LOGFILE,
            mode="a",
            encoding=get_encoding())
        formatter = logging.Formatter(LOGGING_FORMAT)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


class Component(object):

    '''base class for CGATReport components.
    '''

    # options exported to sphinx
    options = ()

    def __init__(self, *args, **kwargs):
        self.logger = get_logger()

    def debug(self, msg):
        self.logger.debug(force_encode("disp%s: %s" % (id(self), msg)))

    def warn(self, msg):
        self.logger.warning(force_encode("disp%s: %s" % (id(self), msg)))

    def warning(self, msg):
        self.logger.warning(force_encode("disp%s: %s" % (id(self), msg)))

    def info(self, msg):
        self.logger.info(force_encode("disp%s: %s" % (id(self), msg)))

    def error(self, msg):
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        tb = "\n".join(traceback.format_tb(exceptionTraceback))
        self.logger.error("disp{}: {}: {} {}\n{}".format(
            id(self),
            msg,
            exceptionType,
            exceptionValue,
            tb))

    def critical(self, msg):
        self.logger.critical("disp%s: %s" % (id(self), msg))
