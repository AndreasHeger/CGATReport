from .Logger import warn, debug, info
from . import Logger
import multiprocessing

Logger.basicConfig(
    level=Logger.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    filename="logger_test.log")


def test_logging(args):
    msg = args[0]
    info(msg)

if __name__ == "__main__":

    #
    #   call from main process to make sure works
    #
    info("starting")

    #
    #   call from child processes in pool
    #
    # start 4 worker processes
    pool = multiprocessing.Pool(processes=4)
    function_parameters = list()
    for a in range(200):
        function_parameters.append(("message #%3d" % a,))
    pool.map(test_logging, function_parameters)

    print(Logger.getCounts())
