import multiprocessing
import logging
import sys
import re
import os
import io
import threading
import time
import collections

# Python 2/3 Compatibility
try:
    import queue
except ImportError:
    import Queue as queue

from logging import Logger


class MultiProcessingLogHandler(logging.Handler):

    """taken from http://stackoverflow.com/questions/641420/how-should-i-log-while-using-multiprocessing-in-python

    added counting of log messages.
    """

    def __init__(self, handler, queue, child=False):
        logging.Handler.__init__(self)

        self._handler = handler
        self.queue = queue

        self.counts = collections.defaultdict(int)

        # we only want one of the loggers to be pulling from the queue.
        # If there is a way to do this without needing to be passed this
        # information, that would be great!
        if child == False:
            self.shutdown = False
            self.polltime = 1
            t = threading.Thread(target=self.receive)
            t.daemon = True
            t.start()

    def setFormatter(self, fmt):
        logging.Handler.setFormatter(self, fmt)
        self._handler.setFormatter(fmt)

    def receive(self):
        while (self.shutdown == False) or (self.queue.empty() == False):
            # so we block for a short period of time so that we can
            # check for the shutdown cases.
            try:
                record = self.queue.get(True, self.polltime)
                self._handler.emit(record)
                self.counts[record.levelname] += 1
            except queue.Empty as e:
                pass
            except EOFError as e:
                break

    def send(self, s):
        # send just puts it in the queue for the server to retrieve
        self.queue.put(s)

    def _format_record(self, record):
        ei = record.exc_info
        if ei:
            # just to get traceback text into record.exc_text
            dummy = self.format(record)
            record.exc_info = None  # to avoid Unpickleable error

        return record

    def emit(self, record):
        try:
            s = self._format_record(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        # give some time for messages to enter the queue.
        time.sleep(self.polltime + 1)
        self.shutdown = True
        # give some time for the server to time out and see the shutdown
        time.sleep(self.polltime + 1)

    def __del__(self):
        # hopefully this aids in orderly shutdown when things are going poorly.
        self.close()

    def getCounts(self):
        return self.counts


def f(x):
    # just a logging command...
    logging.critical('function number: ' + str(x))
    # to make some calls take longer than others, so the output is "jumbled"
    # as real MP programs are.
    time.sleep(x % 3)


def initPool(queue, level):
    """
    This causes the logging module to be initialized with the necessary info
    in pool threads to work correctly.
    """
    logging.getLogger('').addHandler(
        MultiProcessingLogHandler(logging.StreamHandler(), queue, child=True))
    logging.getLogger('').setLevel(level)

if __name__ == '__main__':

    use_stream = False

    if use_stream:
        stream = io.StringIO()
        logQueue = multiprocessing.Queue(100)
        handler = MultiProcessingLogHandler(
            logging.StreamHandler(stream), logQueue)
        logging.getLogger('').addHandler(handler)
        logging.getLogger('').setLevel(logging.DEBUG)

        logging.debug('starting main')

        # when bulding the pool on a Windows machine we also have to init the
        # logger in all the instances with the queue and the level of logging.
        pool = multiprocessing.Pool(processes=10, initializer=initPool, initargs=[
                                    logQueue, logging.getLogger('').getEffectiveLevel()])  # start worker processes
        pool.map(f, list(range(0, 50)))
        pool.close()

        logging.debug('done')
        logging.shutdown()
        print("stream output is:")
        print(stream.getvalue())
    else:
        logQueue = multiprocessing.Queue(100)
        handler = MultiProcessingLogHandler(
            logging.FileHandler("test.log", "w"), logQueue)
        # logging.setLoggerClass(CountedLogger)
        #logging.root = CountedLogger("")
        # print dir(logging.getLogger(''))
        # print logging.getLogger("").getCounts()
        logging.getLogger('').addHandler(handler)
        logging.getLogger('').setLevel(logging.DEBUG)

        logging.debug('starting main')

        # when bulding the pool on a Windows machine we also have to init the
        # logger in all the instances with the queue and the level of logging.
        pool = multiprocessing.Pool(processes=10, initializer=initPool, initargs=[
                                    logQueue, logging.getLogger('').getEffectiveLevel()])  # start worker processes
        pool.map(f, list(range(0, 10)))
        pool.close()

        logging.debug('done')
        logging.shutdown()

        print(handler.getCounts())
