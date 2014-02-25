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

class sphinxreporterror_node(nodes.warning, nodes.Element): pass
class sphinxreporterrorlist(nodes.General, nodes.Element): pass

class SphinxreportError(Directive):
    """
    A sphinxreporterror entry, displayed (if configured) in the form of an admonition.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        targetid = "sphinxreporterror-%s" % env.new_serialno('sphinxreporterror')
        # env.index_num += 1
        targetnode = nodes.target('', '', ids=[targetid])

        # this sets the formatting
        self.options["class"] = "critical"

        if len(self.arguments) > 0:
            errorclass = self.arguments[0]
        else:
            errorclass = "generic"

        ad = make_admonition(sphinxreporterror_node,
                             self.name,
                             [_('SphinxreportError')],
                             self.options,
                             self.content, self.lineno, self.content_offset,
                             self.block_text, self.state, self.state_machine)

        # Attach a list of all sphinxreporterrors to the environment,
        # the sphinxreporterrorlist works with the collected sphinxreporterror nodes
        if not hasattr(env, 'sphinxreporterror_all_sphinxreporterrors'):
            env.sphinxreporterror_all_sphinxreporterrors = []
        env.sphinxreporterror_all_sphinxreporterrors.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'sphinxreporterror': ad[0].deepcopy(),
            'errorclass': errorclass,
            'target': targetnode,
        })

        return [targetnode] + ad


class SphinxreportErrorList(Directive):
    """
    A list of all sphinxreporterror entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        # Simply insert an empty sphinxreporterrorlist node which will be replaced later
        # when process_sphinxreporterror_nodes is called
        return [sphinxreporterrorlist('')]


def process_sphinxreporterror_nodes(app, doctree, fromdocname):
    if not app.config['sphinxreport_show_errors']:
        for node in doctree.traverse(sphinxreporterror_node):
            node.parent.remove(node)

    # Replace all sphinxreporterrorlist nodes with a list of the collected sphinxreporterrors.
    # Augment each sphinxreporterror with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'sphinxreporterror_all_sphinxreporterrors'):
        env.sphinxreporterror_all_sphinxreporterrors = []

    for node in doctree.traverse(sphinxreporterrorlist):
        if not app.config['sphinxreport_show_errors']:
            node.replace_self([])
            continue

        content = []
        nerrors = 0

        para = nodes.paragraph()
        para += nodes.Text("There are %i errors" % len(env.sphinxreporterror_all_sphinxreporterrors))
        content.append(para)

        #table = nodes.enumerated_list()
        #table['enumtype'] = 'arabic'

        for sphinxreporterror_info in env.sphinxreporterror_all_sphinxreporterrors:

            para = nodes.paragraph()

            filename = env.doc2path(sphinxreporterror_info['docname'], base=None)

            nerrors += 1
            location_str = '%s:%d ' % (filename, sphinxreporterror_info['lineno'])
            try:
                description_str = sphinxreporterror_info['errorclass']
            except KeyError:
                description_str = "unknown"

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_(location_str), _(location_str))
            newnode['refdocname'] = sphinxreporterror_info['docname']
            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, sphinxreporterror_info['docname'])
                newnode['refuri'] += '#' + sphinxreporterror_info['target']['refid']
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

            # (Recursively) resolve references in the sphinxreporterror content
            sphinxreporterror_entry = sphinxreporterror_info['sphinxreporterror']
            env.resolve_references(sphinxreporterror_entry, sphinxreporterror_info['docname'],
                                   app.builder)

            # add item to table
            # table += i
            content.append(para)

        #content.append(table)

        node.replace_self(content)


def purge_sphinxreporterrors(app, env, docname):
    if not hasattr(env, 'sphinxreporterror_all_sphinxreporterrors'):
        return
    env.sphinxreporterror_all_sphinxreporterrors = [sphinxreporterror for sphinxreporterror in env.sphinxreporterror_all_sphinxreporterrors
                          if sphinxreporterror['docname'] != docname]


def visit_sphinxreporterror_node(self, node):
    self.visit_admonition(node)

def depart_sphinxreporterror_node(self, node):
    self.depart_admonition(node)

def setup(app):
    app.add_config_value('sphinxreport_show_errors', True, False)

    app.add_node(sphinxreporterrorlist)
    app.add_node(sphinxreporterror_node,
                 html=(visit_sphinxreporterror_node, depart_sphinxreporterror_node),
                 latex=(visit_sphinxreporterror_node, depart_sphinxreporterror_node),
                 text=(visit_sphinxreporterror_node, depart_sphinxreporterror_node))

    app.add_directive('error', SphinxreportError)
    app.add_directive('errorlist', SphinxreportErrorList)
    app.connect('doctree-resolved', process_sphinxreporterror_nodes)
    app.connect('env-purge-doc', purge_sphinxreporterrors)

