import re

from docutils import nodes, utils
from docutils.parsers.rst import roles

from sphinx import addnodes
from sphinx.util import ws_re, caption_ref_re

from SphinxReport import Utils

default_settings = {
    'pubmed_url' : "http://www.ncbi.nlm.nih.gov/pubmed/%i" }

def pmid_reference_role(role, rawtext, text, lineno, inliner,
                       options={}, content=[]):
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

def param_role( role, rawtext, text, lineno, inliner,
                options={}, content=[]):
    
    parts = text.split(".")

    if len(parts) < 2:
        msg = inliner.reporter.error(
            ':param: should be in class.value format '
            ': "%s" is invalid.' % text, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    class_name, parameter_name = ".".join(parts[:-1]), parts[-1]

    try:
        code, tracker = Utils.makeTracker( class_name )
    except AttributeError:
        tracker = None

    if not tracker:
        msg = inliner.reporter.error(
            ':param: can not find class '
            '"%s".' % class_name, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    try:
        value = getattr( tracker, parameter_name )
    except AttributeError:
        msg = inliner.reporter.error(
            ':param: can not find variable %s in '
            ': "%s" is invalid -tracker=%s.' % (parameter_name, class_name, str(tracker)), line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    # Base URL mainly used by inliner.rfc_reference, so this is correct:
    # ref = inliner.document.settings.rfc_base_url + inliner.rfc_url % value
    # in example, but deprecated
    # set_classes(options)
    node = nodes.literal(rawtext, 
                        utils.unescape(str(value)), 
                        **options)

    return [node], []

def value_role( role, rawtext, text, lineno, inliner,
                options={}, content=[]):
    
    class_name = text

    try:
        code, tracker = Utils.makeTracker( class_name )
    except (AttributeError, ImportError):
        tracker = None

    if not tracker:
        msg = inliner.reporter.error(
            ':value: can not find class '
            '"%s".' % class_name, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    value = str( tracker() )

    # Base URL mainly used by inliner.rfc_reference, so this is correct:
    # ref = inliner.document.settings.rfc_base_url + inliner.rfc_url % value
    # in example, but deprecated
    # set_classes(options)
    node = nodes.literal(rawtext, 
                        utils.unescape(str(value)), 
                        **options)

    return [node], []

roles.register_local_role('pmid', pmid_reference_role)
roles.register_local_role('param', param_role)
roles.register_local_role('value', value_role)

def setup( self ):
    pass
