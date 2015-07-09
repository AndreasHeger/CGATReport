# -*- coding: utf-8 -*-
"""
    sphinx.ext.warnings
    ~~~~~~~~~~~~~~~~~~~

    Collect all warnings

:copyright: Copyright 2007-2009 by the Andreas Heger, see AUTHORS.
:license: BSD, see LICENSE for details.
"""

import logging
from docutils import nodes

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.compat import Directive
from docutils.parsers.rst.directives.admonitions import BaseAdmonition


class cgatreportwarning_node(nodes.warning, nodes.Element):
    pass


class cgatreportwarninglist(nodes.General, nodes.Element):
    pass


class CGATReportWarning(BaseAdmonition):

    node_class = cgatreportwarning_node

    # accept error as an optional argument
    optional_arguments = 1

    def run(self):

        r = BaseAdmonition.run(self)

        if len(self.arguments) > 0:
            warningclass = self.arguments[0]
        else:
            warningclass = "generic"

        env = self.state.document.settings.env
        if not hasattr(env, 'cgatreportwarning_all_cgatreportwarnings'):
            env.cgatreportwarning_all_cgatreportwarnings = []

        env.cgatreportwarning_all_cgatreportwarnings.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'cgatreportwarning': r[0].deepcopy(),
            'warningclass': warningclass,
        })

        logging.warn("CGATReport-Warning: %s" % warningclass)

        return r


class CGATReportWarningList(Directive):

    """
    A list of all cgatreportwarning entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        # Simply insert an empty cgatreportwarninglist node which will
        # be replaced later when process_cgatreportwarning_nodes is
        # called
        return [cgatreportwarninglist('')]


def process_cgatreportwarning_nodes(app, doctree, fromdocname):
    if not app.config['cgatreport_show_warnings']:
        for node in doctree.traverse(cgatreportwarning_node):
            node.parent.remove(node)

    # Replace all cgatreportwarninglist nodes with a list of the
    # collected cgatreportwarnings.  Augment each cgatreportwarning
    # with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'cgatreportwarning_all_cgatreportwarnings'):
        env.cgatreportwarning_all_cgatreportwarnings = []

    for node in doctree.traverse(cgatreportwarninglist):
        if not app.config['cgatreport_show_warnings']:
            node.replace_self([])
            continue

        content = []
        nwarnings = 0

        para = nodes.paragraph()
        para += nodes.Text("There are %i warnings" %
                           len(env.cgatreportwarning_all_cgatreportwarnings))
        content.append(para)

        for cgatreportwarning_info in env.cgatreportwarning_all_cgatreportwarnings:

            para = nodes.paragraph()

            filename = env.doc2path(
                cgatreportwarning_info['docname'], base=None)

            nwarnings += 1
            location_str = '%s:%d ' % (
                filename, cgatreportwarning_info['lineno'])
            try:
                description_str = cgatreportwarning_info['warningclass']
            except KeyError:
                description_str = "unknown"

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_(location_str), _(location_str))
            newnode['refdocname'] = cgatreportwarning_info['docname']

            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, cgatreportwarning_info['docname'])
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass
            newnode.append(innernode)

            para += newnode
            para += nodes.Text(description_str, description_str)
            para += nodes.Text("\n", "\n")

            # (Recursively) resolve references in the cgatreportwarning content
            cgatreportwarning_entry = cgatreportwarning_info[
                'cgatreportwarning']
            env.resolve_references(cgatreportwarning_entry,
                                   cgatreportwarning_info['docname'],
                                   app.builder)

            content.append(para)

        node.replace_self(content)


def purge_cgatreportwarnings(app, env, docname):
    if not hasattr(env, 'cgatreportwarning_all_cgatreportwarnings'):
        return
    env.cgatreportwarning_all_cgatreportwarnings = \
        [cgatreportwarning for cgatreportwarning in
         env.cgatreportwarning_all_cgatreportwarnings
         if cgatreportwarning['docname'] != docname]


def visit_cgatreportwarning_node(self, node):
    self.visit_admonition(node)


def depart_cgatreportwarning_node(self, node):
    self.depart_admonition(node)


def setup(app):
    app.add_config_value('cgatreport_show_warnings', True, False)

    app.add_node(cgatreportwarninglist)
    app.add_node(cgatreportwarning_node,
                 html=(visit_cgatreportwarning_node,
                       depart_cgatreportwarning_node),
                 latex=(
                     visit_cgatreportwarning_node,
                     depart_cgatreportwarning_node),
                 text=(visit_cgatreportwarning_node,
                       depart_cgatreportwarning_node))

    app.add_directive('warning', CGATReportWarning)
    app.add_directive('warninglist', CGATReportWarningList)
    app.connect('doctree-resolved', process_cgatreportwarning_nodes)
    app.connect('env-purge-doc', purge_cgatreportwarnings)
