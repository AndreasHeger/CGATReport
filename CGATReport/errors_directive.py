# -*- coding: utf-8 -*-
"""
    sphinx.ext.errors
    ~~~~~~~~~~~~~~~~~

    Collect all errors

:copyright: Copyright 2007-2009 by the Andreas Heger, see AUTHORS.
:license: BSD, see LICENSE for details.
"""

from docutils import nodes
import os
import logging

from docutils.parsers.rst import Directive
from sphinx.locale import _
from sphinx.environment import NoUri
from docutils.parsers.rst.directives.admonitions import BaseAdmonition
import shelve

CGATREPORT_ERRORS_CACHE = "cgatreport_errors.cache"


class cgatreporterror_node(nodes.warning, nodes.Element):
    pass


class cgatreporterrorlist(nodes.General, nodes.Element):
    pass


class CGATReportError(BaseAdmonition):

    node_class = cgatreporterror_node

    # accept error as an optional argument
    optional_arguments = 1

    def run(self):

        r = BaseAdmonition.run(self)

        if len(self.arguments) > 0:
            errorclass = self.arguments[0]
        else:
            errorclass = "generic"

        env = self.state.document.settings.env

        error_cache = shelve.open(CGATREPORT_ERRORS_CACHE)

        error_cache["{}:{:06}".format(env.docname, self.lineno)] = (
            r[0].deepcopy(), errorclass)

        logging.error("CGATReport-Error: %s" % errorclass)

        return r


class CGATReportErrorList(Directive):

    """
    A list of all cgatreporterror entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        # Simply insert an empty cgatreporterrorlist node which will
        # be replaced later when process_cgatreporterror_nodes is
        # called
        return [cgatreporterrorlist('')]


def process_cgatreporterror_nodes(app, doctree, fromdocname):

    if not app.config['cgatreport_show_errors']:
        for node in doctree.traverse(cgatreporterror_node):
            node.parent.remove(node)

    # Replace all cgatreporterrorlist nodes with a list of the
    # collected cgatreporterrors.  Augment each cgatreporterror with a
    # backlink to the original location.
    env = app.builder.env

    error_cache = shelve.open(CGATREPORT_ERRORS_CACHE)

    for node in doctree.traverse(cgatreporterrorlist):

        if not app.config['cgatreport_show_errors']:
            node.replace_self([])
            continue

        nerrors = 0

        content = []

        para = nodes.paragraph()
        sorted_items = sorted(error_cache.items())
        para += nodes.Text("There are {} errors".format(len(sorted_items)))

        content.append(para)

        for key, value in sorted_items:

            docname, lineno = key.split(":")
            lineno = int(lineno)
            cgatreporterror, errorclass = value

            para = nodes.paragraph()

            filename = env.doc2path(docname, base=None)

            nerrors += 1
            location_str = '%s:%d ' % (filename, lineno)

            try:
                description_str = errorclass
            except KeyError:
                description_str = "unknown"

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis((location_str), (location_str))
            newnode['refdocname'] = docname
            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, docname)
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass

            newnode.append(innernode)

            para += newnode
            para += nodes.Text(description_str, description_str)
            para += nodes.Text("\n", "\n")

            # (Recursively) resolve references in the cgatreporterror content
            env.resolve_references(cgatreporterror,
                                   docname,
                                   app.builder)

            content.append(para)

        node.replace_self(content)


def purge_cgatreporterrors(app, env, docname):
    if not hasattr(env, 'cgatreporterror_all_cgatreporterrors'):
        return
    env.cgatreporterror_all_cgatreporterrors = \
        [cgatreporterror for cgatreporterror in
         env.cgatreporterror_all_cgatreporterrors
         if cgatreporterror['docname'] != docname]


def visit_cgatreporterror_node(self, node):
    self.visit_admonition(node)


def depart_cgatreporterror_node(self, node):
    self.depart_admonition(node)


def setup(app):
    app.add_config_value('cgatreport_show_errors', True, False)

    app.add_node(cgatreporterrorlist)
    app.add_node(
        cgatreporterror_node,
        html=(
            visit_cgatreporterror_node, depart_cgatreporterror_node),
        latex=(
            visit_cgatreporterror_node,
            depart_cgatreporterror_node),
        text=(visit_cgatreporterror_node, depart_cgatreporterror_node))

    app.add_directive('error', CGATReportError)
    app.add_directive('errorlist', CGATReportErrorList)
    app.connect('doctree-resolved', process_cgatreporterror_nodes)
    app.connect('env-purge-doc', purge_cgatreporterrors)

    try:
        os.unlink(CGATREPORT_ERRORS_CACHE)
    except OSError:
        pass

    return {'parallel_read_safe': True}
