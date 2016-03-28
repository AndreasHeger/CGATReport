'''basic module for CGATReport actors.
'''

import pkg_resources
import logging
import collections
from docutils.parsers.rst import directives

LOGFILE = "cgatreport.log"
LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'

def get_logger():

    logger = logging.getLogger(
        "cgatreport")

    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(
            LOGFILE,
            mode="a")
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
        self.logger.debug("disp%s: %s" % (id(self), msg))

    def warn(self, msg):
        self.logger.warn("disp%s: %s" % (id(self), msg))

    def info(self, msg):
        self.logger.info("disp%s: %s" % (id(self), msg))

    def error(self, msg):
        self.logger.error("disp%s: %s" % (id(self), msg))

    def critical(self, msg):
        self.logger.critical("disp%s: %s" % (id(self), msg))

# plugins are only initialized once they are called
# for in order to remove problems with cyclic imports
plugins = None
options = None
ENTRYPOINT = 'CGATReport.plugins'


def init_plugins():

    logger = get_logger()

    logger.info("initialising plugins")
    try:
        pkg_resources.working_set.add_entry(cgatreport_plugins)
        pkg_env = pkg_resources.Environment(cgatreport_plugins)
    except NameError:
        pkg_env = pkg_resources.Environment()

    plugins = collections.defaultdict(dict)
    for name in pkg_env:
        egg = pkg_env[name][0]
        egg.activate()
        for name in egg.get_entry_map(ENTRYPOINT):
            entry_point = egg.get_entry_info(ENTRYPOINT, name)
            cls = entry_point.load()
            if not hasattr(cls, 'capabilities'):
                cls.capabilities = []

            for c in cls.capabilities:
                plugins[c][name] = cls

    if len(plugins) == 0:
        logger.warn("did not find any plugins")
    else:
        logger.debug(
            "found plugins: %i capabilites and %i plugins" %
            (len(plugins), sum([len(x) for x in list(plugins.values())])))

    return plugins


def getPlugins(capability=None):
    global plugins
    if not plugins:
        plugins = init_plugins()
    if capability is None:
        return plugins
        result = set()
        for p in plugins.values():
            for plugin in p:
                result.add(plugin)
        return list(result)
    else:
        return plugins.get(capability, {})


def getOptionMap():
    global options

    if options is None:
        options = {}
        for section, plugins in getPlugins().items():
            options[section] = {}
            for name, cls in plugins.items():
                try:
                    options[section].update(dict(cls.options))
                except AttributeError:
                    pass

        options["dispatch"] = {
            'groupby': directives.unchanged,
            'set-index': directives.unchanged,
            'include-columns': directives.unchanged,
            'exclude-columns': directives.unchanged,
            'tracks': directives.unchanged,
            'slices': directives.unchanged,
            'layout': directives.unchanged,
            'restrict': directives.unchanged,
            'exclude': directives.unchanged,
            'nocache': directives.flag,
        }

        # options used in trackers
        options["tracker"] = {
            'regex': directives.unchanged,
            'glob': directives.unchanged,
            'sql_backend': directives.unchanged,
        }

        options["display"] = {
            # general image options
            'alt': directives.unchanged,
            'height': directives.length_or_unitless,
            'width': directives.length_or_percentage_or_unitless,
            'scale': directives.nonnegative_int,
            'class': directives.class_option,
            # 'align': align,
            # options for cgatreport
            'render': directives.unchanged,
            'transform': directives.unchanged,
            'display': directives.unchanged,
            'extra-formats': directives.unchanged,
            'no-caption': directives.flag,
            'no-title': directives.flag,
            'no-links': directives.flag,
        }

    return options


def getOptionSpec():
    '''build option spec for sphinx

    This method returns a flattened :var:`options`
    dictionary.
    '''
    o = getOptionMap()
    r = {}
    for x, xx in o.items():
        r.update(xx)

    # add the primary actor options
    r["render"] = directives.unchanged
    r["transform"] = directives.unchanged
    return r
