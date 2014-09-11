# -*- coding: utf-8 -*-
"""
    sphinx.ext.errors
    ~~~~~~~~~~~~~~~~~

    Collect all errors

:copyright: Copyright 2007-2009 by the Andreas Heger, see AUTHORS.
:license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.compat import Directive, make_admonition


class cgatreporterror_node(nodes.warning, nodes.Element):
    pass


class cgatreporterrorlist(nodes.General, nodes.Element):
    pass


class CGATReportError(Directive):

    """
    A cgatreporterror entry, displayed (if configured) in the form of an admonition.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        targetid = "cgatreporterror-%s" % env.new_serialno(
            'cgatreporterror')
        # env.index_num += 1
        targetnode = nodes.target('', '', ids=[targetid])

        # this sets the formatting
        self.options["class"] = "critical"

        if len(self.arguments) > 0:
            errorclass = self.arguments[0]
        else:
            errorclass = "generic"

        ad = make_admonition(cgatreporterror_node,
                             self.name,
                             [_('CGATReportError')],
                             self.options,
                             self.content, self.lineno, self.content_offset,
                             self.block_text, self.state, self.state_machine)

        # Attach a list of all cgatreporterrors to the environment,
        # the cgatreporterrorlist works with the collected cgatreporterror
        # nodes
        if not hasattr(env, 'cgatreporterror_all_cgatreporterrors'):
            env.cgatreporterror_all_cgatreporterrors = []
        env.cgatreporterror_all_cgatreporterrors.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'cgatreporterror': ad[0].deepcopy(),
            'errorclass': errorclass,
            'target': targetnode,
        })

        return [targetnode] + ad


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
        # Simply insert an empty cgatreporterrorlist node which will be replaced later
        # when process_cgatreporterror_nodes is called
        return [cgatreporterrorlist('')]


def process_cgatreporterror_nodes(app, doctree, fromdocname):
    if not app.config['cgatreport_show_errors']:
        for node in doctree.traverse(cgatreporterror_node):
            node.parent.remove(node)

    # Replace all cgatreporterrorlist nodes with a list of the collected cgatreporterrors.
    # Augment each cgatreporterror with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'cgatreporterror_all_cgatreporterrors'):
        env.cgatreporterror_all_cgatreporterrors = []

    for node in doctree.traverse(cgatreporterrorlist):
        if not app.config['cgatreport_show_errors']:
            node.replace_self([])
            continue

        content = []
        nerrors = 0

        para = nodes.paragraph()
        para += nodes.Text("There are %i errors" %
                           len(env.cgatreporterror_all_cgatreporterrors))
        content.append(para)

        #table = nodes.enumerated_list()
        #table['enumtype'] = 'arabic'

        for cgatreporterror_info in env.cgatreporterror_all_cgatreporterrors:

            para = nodes.paragraph()

            filename = env.doc2path(
                cgatreporterror_info['docname'], base=None)

            nerrors += 1
            location_str = '%s:%d ' % (
                filename, cgatreporterror_info['lineno'])
            try:
                description_str = cgatreporterror_info['errorclass']
            except KeyError:
                description_str = "unknown"

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_(location_str), _(location_str))
            newnode['refdocname'] = cgatreporterror_info['docname']
            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, cgatreporterror_info['docname'])
                newnode['refuri'] += '#' + \
                    cgatreporterror_info['target']['refid']
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass
            newnode.append(innernode)

            para += newnode
            para += nodes.Text(description_str, description_str)
            para += nodes.Text("\n", "\n")

            # could not get a list to work - the list was created
            # with the correct numbers of items, but there was no
            # text.
            # i= nodes.list_item("sthtsnh")

            # (Recursively) resolve references in the cgatreporterror content
            cgatreporterror_entry = cgatreporterror_info[
                'cgatreporterror']
            env.resolve_references(cgatreporterror_entry, cgatreporterror_info['docname'],
                                   app.builder)

            # add item to table
            # table += i
            content.append(para)

        # content.append(table)

        node.replace_self(content)


def purge_cgatreporterrors(app, env, docname):
    if not hasattr(env, 'cgatreporterror_all_cgatreporterrors'):
        return
    env.cgatreporterror_all_cgatreporterrors = [cgatreporterror for cgatreporterror in env.cgatreporterror_all_cgatreporterrors
                                                    if cgatreporterror['docname'] != docname]


def visit_cgatreporterror_node(self, node):
    self.visit_admonition(node)


def depart_cgatreporterror_node(self, node):
    self.depart_admonition(node)


def setup(app):
    app.add_config_value('cgatreport_show_errors', True, False)

    app.add_node(cgatreporterrorlist)
    app.add_node(cgatreporterror_node,
                 html=(
                     visit_cgatreporterror_node, depart_cgatreporterror_node),
                 latex=(
                     visit_cgatreporterror_node, depart_cgatreporterror_node),
                 text=(visit_cgatreporterror_node, depart_cgatreporterror_node))

    app.add_directive('error', CGATReportError)
    app.add_directive('errorlist', CGATReportErrorList)
    app.connect('doctree-resolved', process_cgatreporterror_nodes)
    app.connect('env-purge-doc', purge_cgatreporterrors)
