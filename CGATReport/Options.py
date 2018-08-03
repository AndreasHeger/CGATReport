"""set and manipulate options for Capabilities.
"""
import re

from docutils.parsers.rst import directives

from CGATReport.Capabilities import get_all_plugins
from CGATReport.Utils import get_params


OPTIONS = None


def get_option_map():

    global OPTIONS

    if OPTIONS is None:
        OPTIONS = {}
        for section, plugins in get_all_plugins().items():
            OPTIONS[section] = {}
            for name, cls in list(plugins.items()):
                try:
                    OPTIONS[section].update(dict(cls.options))
                except AttributeError:
                    pass

        OPTIONS["dispatch"] = {
            'groupby': directives.unchanged,
            'set-index': directives.unchanged,
            'include-columns': directives.unchanged,
            'exclude-columns': directives.unchanged,
            'tracks': directives.unchanged,
            'slices': directives.unchanged,
            'paths': directives.unchanged,
            'layout': directives.unchanged,
            'long-titles': directives.flag,
            'restrict': directives.unchanged,
            'exclude': directives.unchanged,
            'nocache': directives.flag,
        }

        # options used in trackers
        OPTIONS["tracker"] = {
            'regex': directives.unchanged,
            'glob': directives.unchanged,
            'filename': directives.unchanged,
            'sql_backend': directives.unchanged,
            'tracker': directives.unchanged,
        }

        OPTIONS["display"] = {
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

    return OPTIONS


def get_option_spec():
    '''build option spec for sphinx

    This method returns a flattened :var:`options`
    dictionary.
    '''
    r = {}
    for x, xx in get_option_map().items():
        r.update(xx)

    # add the primary actor options
    r["render"] = directives.unchanged
    r["transform"] = directives.unchanged
    return r


def update_options(kwargs):
    '''replace placeholders in kwargs with with PARAMS read from config file.

    returns the update dictionary.
    '''

    params = get_params()

    for key, value in list(kwargs.items()):
        try:
            v = value.strip()
        except AttributeError:
            # ignore non-string types
            continue
            
        last_end = 0
        parts = []
        for match in re.finditer("@([^@]+)@", v):
            code = v[match.start() + 1:match.end() - 1]
            if code not in params:
                raise ValueError("unknown placeholder `%s`" % code)
            parts.append(v[last_end:match.start()])
            parts.append(params[code])
            last_end = match.end()
        parts.append(v[last_end:])
        kwargs[key] = "".join(map(str, parts))

    return kwargs


def expand_option(option):
    """expand option that is a ',' separated list of assignments.
    """
    kwargs = {}
    option = option.strip()
    if len(option) == 0:
        return kwargs
    parts = option.split(",")

    for part in parts:
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError("malformed tracker options '{}' in '{}'".format(part, option))
        key, val = part.split("=", 1)
        try:
            kwargs[key.strip()] = eval(val.strip())
        except NameError:
            kwargs[key.strip()] = val

    return kwargs


def select_and_delete_options(options, select, expand=[]):
    '''collect options in *select* and from *options* and remove those found.

    expand is a list of keywards that will be expanded.

    returns dictionary of options found.
    '''
    new_options = {}
    for k, v in options.items():
        if k in select:
            new_options[k] = v
    for k in new_options.keys():
        del options[k]

    for k in expand:
        if k in new_options:
            new_options.update(expand_option(new_options[k]))
    return new_options
