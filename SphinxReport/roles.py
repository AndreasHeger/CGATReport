import re
import os
import sys

from docutils import nodes, utils
from docutils.parsers.rst import roles, directives

from sphinx import addnodes
from sphinx.util import ws_re, caption_ref_re

from SphinxReport import Utils

default_settings = {
    'pubmed_url': "http://www.ncbi.nlm.nih.gov/pubmed/%i"}


def writeCode(class_name, code, inliner):
    '''write code of class to file.

    returns URI of written code.
    '''
    document = inliner.document.current_source

    reference = class_name

    # root of document tree
    srcdir = setup.srcdir

    # build directory
    builddir = setup.confdir

    # get the directory of the rst file
    rstdir, rstfile = os.path.split(document)

    basedir, fname, basename, ext, outdir, codename, notebookname = Utils.buildPaths(
        reference)

    # path to root relative to rst
    rst2srcdir = os.path.join(os.path.relpath(srcdir, start=rstdir), outdir)

    # output code
    linked_codename = re.sub("\\\\", "/", os.path.join(rst2srcdir, codename))
    if code and basedir != outdir:
        outfile = open(os.path.join(outdir, codename), "w")
        for line in code:
            outfile.write(line)
        outfile.close()

    return linked_codename


def pmid_reference_role(role, rawtext, text, lineno, inliner,
                        options={}, content=[]):
    '''insert a link to pubmed into the text.'''
    try:
        pmid = int(text)
        if pmid <= 0:
            raise ValueError
    except ValueError:
        msg = inliner.reporter.error(
            'pmid number must be a number greater than or equal to 1; '
            '"%s" is invalid.' % text, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    # Base URL mainly used by inliner.rfc_reference, so this is correct:
    ref = default_settings["pubmed_url"] % pmid
    # in example, but deprecated
    # set_classes(options)
    node = nodes.reference(rawtext, 'PMID ' + utils.unescape(text), refuri=ref,
                           **options)

    return [node], []


def param_role(role, rawtext, text, lineno, inliner,
               options={}, content=[]):
    '''inserts a member variable of a tracker class in the text.'''

    parts = text.split(".")

    if len(parts) < 2:
        msg = inliner.reporter.error(
            ':param: should be in class.value format '
            ': "%s" is invalid.' % text, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    class_name, parameter_name = ".".join(parts[:-1]), parts[-1]

    try:
        code, tracker = Utils.makeTracker(class_name)
    except AttributeError:
        tracker = None

    if not tracker:
        msg = inliner.reporter.error(
            ':param: can not find class '
            '"%s".' % class_name, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    try:
        value = getattr(tracker, parameter_name)
    except AttributeError:
        msg = inliner.reporter.error(
            ':param: can not find variable %s in '
            ': "%s" is invalid -tracker=%s.' % (parameter_name, class_name, str(tracker)), line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    linked_codename = writeCode(class_name, code, inliner)

    node = nodes.reference(rawtext,
                           utils.unescape(str(value)),
                           refuri=linked_codename,
                           **options)

    return [node], []


def value_role(role, rawtext, text, lineno, inliner,
               options={}, content=[]):
    '''insert a single value from a tracker into text.'''

    class_name = text

    try:
        code, tracker = Utils.makeTracker(class_name)
    except (AttributeError, ImportError):
        tracker = None

    if not tracker:
        msg = inliner.reporter.error(
            ':value: can not find class '
            '"%s".' % class_name, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    # Python 2/3
    try:
        value = str(tracker())
    except TypeError as msg:
        print("python 3 problem: %s: tracker=%s" % (msg, str(tracker())))

    linked_codename = writeCode(class_name, code, inliner)

    # Base URL mainly used by inliner.rfc_reference, so this is correct:
    # ref = inliner.document.settings.rfc_base_url + inliner.rfc_url % value
    # in example, but deprecated
    # set_classes(options)
    # node = nodes.literal(rawtext,
    #                    utils.unescape(str(value)),
    #                   **options)
    node = nodes.reference(rawtext,
                           utils.unescape(str(value)),
                           refuri=linked_codename,
                           **options)

    return [node], []


def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir
    setup.srcdir = app.srcdir

roles.register_local_role('pmid', pmid_reference_role)
roles.register_local_role('param', param_role)
roles.register_local_role('value', value_role)

# def setup(self):
#    pass
