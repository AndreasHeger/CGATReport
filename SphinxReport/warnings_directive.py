# -*- coding: utf-8 -*-
"""
    sphinx.ext.warnings
    ~~~~~~~~~~~~~~~~~~~

    Collect all warnings

:copyright: Copyright 2007-2009 by the Andreas Heger, see AUTHORS.
:license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.locale import _
from sphinx.environment import NoUri
from sphinx.util.compat import Directive, make_admonition

class sphinxreportwarning_node(nodes.warning, nodes.Element): pass
class sphinxreportwarninglist(nodes.General, nodes.Element): pass

class SphinxreportWarning(Directive):
    """
    A sphinxreportwarning entry, displayed (if configured) in the form of an admonition.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        targetid = "sphinxreportwarning-%s" % env.new_serialno('sphinxreportwarning')
        # env.index_num += 1
        targetnode = nodes.target('', '', ids=[targetid])

        # this sets the formatting
        self.options["class"] = "critical"

        if len(self.arguments) > 0:
            warningclass = self.arguments[0]
        else:
            warningclass = "generic"

        ad = make_admonition(sphinxreportwarning_node,
                             self.name,
                             [_('SphinxreportWarning')],
                             self.options,
                             self.content, self.lineno, self.content_offset,
                             self.block_text, self.state, self.state_machine)

        # Attach a list of all sphinxreportwarnings to the environment,
        # the sphinxreportwarninglist works with the collected sphinxreportwarning nodes
        if not hasattr(env, 'sphinxreportwarning_all_sphinxreportwarnings'):
            env.sphinxreportwarning_all_sphinxreportwarnings = []
        env.sphinxreportwarning_all_sphinxreportwarnings.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'sphinxreportwarning': ad[0].deepcopy(),
            'warningclass': warningclass,
            'target': targetnode,
        })

        return [targetnode] + ad


class SphinxreportWarningList(Directive):
    """
    A list of all sphinxreportwarning entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        # Simply insert an empty sphinxreportwarninglist node which will be replaced later
        # when process_sphinxreportwarning_nodes is called
        return [sphinxreportwarninglist('')]


def process_sphinxreportwarning_nodes(app, doctree, fromdocname):
    if not app.config['sphinxreport_show_warnings']:
        for node in doctree.traverse(sphinxreportwarning_node):
            node.parent.remove(node)

    # Replace all sphinxreportwarninglist nodes with a list of the collected sphinxreportwarnings.
    # Augment each sphinxreportwarning with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'sphinxreportwarning_all_sphinxreportwarnings'):
        env.sphinxreportwarning_all_sphinxreportwarnings = []

    for node in doctree.traverse(sphinxreportwarninglist):
        if not app.config['sphinxreport_show_warnings']:
            node.replace_self([])
            continue

        content = []
        nwarnings = 0

        para = nodes.paragraph()
        para += nodes.Text("There are %i warnings" % len(env.sphinxreportwarning_all_sphinxreportwarnings))
        content.append(para)

        #table = nodes.enumerated_list()
        #table['enumtype'] = 'arabic'

        for sphinxreportwarning_info in env.sphinxreportwarning_all_sphinxreportwarnings:

            para = nodes.paragraph()

            filename = env.doc2path(sphinxreportwarning_info['docname'], base=None)

            nwarnings += 1
            location_str = '%s:%d ' % (filename, sphinxreportwarning_info['lineno'])
            try:
                description_str = sphinxreportwarning_info['warningclass']
            except KeyError:
                description_str = "unknown"

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_(location_str), _(location_str))
            newnode['refdocname'] = sphinxreportwarning_info['docname']
            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, sphinxreportwarning_info['docname'])
                newnode['refuri'] += '#' + sphinxreportwarning_info['target']['refid']
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

            # (Recursively) resolve references in the sphinxreportwarning content
            sphinxreportwarning_entry = sphinxreportwarning_info['sphinxreportwarning']
            env.resolve_references(sphinxreportwarning_entry, sphinxreportwarning_info['docname'],
                                   app.builder)

            # add item to table
            # table += i
            content.append(para)

        #content.append(table)

        node.replace_self(content)


def purge_sphinxreportwarnings(app, env, docname):
    if not hasattr(env, 'sphinxreportwarning_all_sphinxreportwarnings'):
        return
    env.sphinxreportwarning_all_sphinxreportwarnings = [sphinxreportwarning for sphinxreportwarning in env.sphinxreportwarning_all_sphinxreportwarnings
                          if sphinxreportwarning['docname'] != docname]


def visit_sphinxreportwarning_node(self, node):
    self.visit_admonition(node)

def depart_sphinxreportwarning_node(self, node):
    self.depart_admonition(node)

def setup(app):
    app.add_config_value('sphinxreport_show_warnings', True, False)

    app.add_node(sphinxreportwarninglist)
    app.add_node(sphinxreportwarning_node,
                 html=(visit_sphinxreportwarning_node, depart_sphinxreportwarning_node),
                 latex=(visit_sphinxreportwarning_node, depart_sphinxreportwarning_node),
                 text=(visit_sphinxreportwarning_node, depart_sphinxreportwarning_node))

    app.add_directive('warning', SphinxreportWarning)
    app.add_directive('warninglist', SphinxreportWarningList)
    app.connect('doctree-resolved', process_sphinxreportwarning_nodes)
    app.connect('env-purge-doc', purge_sphinxreportwarnings)

