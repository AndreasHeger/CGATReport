#!/bin/env python

"""
cgatreport-serve
==================

:command:`cgatreport-serve` starts a minimalist web server that permits
the user to interact with some of the elements in a sphinxport document. In particular,
it enables the ``data`` element permitting the download of raw data.

To start the server, type::

   cgatreport-serve

in a cgatreport directory. Once a server has started, the documents can
be accessed at from the same host as:

   http://localhost:8080/static

.. note::
   This feature has not been thoroughly tested. In particular, the security implications
   are unclear and the tools should best be used behind a firewall only.

The full list of command line options is listed by suppling:option:`-h/--help`
on the command line.

The options are:

**-t/--html** html dir
   Directory of the report in html format. The default is "_build/html".
   The html directory should contain a file:file:`index.html`. A link
   called ``static`` will be created in the current directory.

**-p/--port** port
   The port to use. The default port is ``8080``. If the port is changed,
   the URL in the example above needs to be changed accordingly.

**-a/--action** action
   Action to perform. The default is to ``start`` the server. Other
   actions are ``stop`` to stop and ``restart`` to restart the server.
"""

import sys
import os
import imp
import io
import re
import types
import glob
import optparse
import shutil

USAGE = """python %s [OPTIONS]

start a cgatreport server

""" % sys.argv[0]


import web

from CGATReport import Utils
from CGATReport import Cache
from CGATReport import DataTree
from collections import OrderedDict as odict


urls = ('/data/(.*)', 'DataTable',
        '/index/(.*)', 'Index')

# expose zip within templates
global_vars = {'zip': zip}

render = web.template.render(
    '%s/' % Utils.getTemplatesDir(), globals=global_vars)

app = web.application(urls, globals())


class DataTable:

    '''render data retrieved from cache as a table.'''

    def GET(self, tracker):

        cache = Cache.Cache(tracker, mode="r")
        data = DataTree.fromCache(cache)
        table, row_headers, col_headers = DataTree.tree2table(data)

        return render.data_table(table, row_headers, col_headers)


def main():

    parser = optparse.OptionParser(version="%prog version: $Id$", usage=USAGE)

    parser.add_option("-p", "--port", dest="port", type="int",
                      help="the port to use [default=%default]")

    parser.add_option("-t", "--html", dest="htmldir", type="string",
                      help="html directory [default=%default]")

    parser.add_option("-a", "--action", dest="action", type="choice",
                      choices=("start", "stop", "restart"),
                      help="action to perform [default=%default]")

    parser.set_defaults(
        htmldir="_build/html",
        port=8080,
        action="start",
    )

    (options, args) = parser.parse_args()

    if options.action == "start":
        # create static link
        if not os.path.exists(options.htmldir):
            raise IOError(
                "html directory %s does not exist, use --html option" % options.htmldir)
        if not os.path.exists(os.path.join(options.htmldir, "index.html")):
            raise IOError(
                "html directory %s has no 'index.html'" % options.htmldir)

        if not os.path.exists("static"):
            os.symlink(options.htmldir, "static")
        else:
            if not os.path.exists(os.path.join("static", "index.html")):
                raise IOError("directory %s has no 'index.html'" % "static")

        # set port
        sys.argv = [sys.argv[0], str(options.port)]
        app.run()
    elif options.action == "stop":
        raise NotImplementedError("stop not implemented - try ctrl-c")
    elif options.action == "restart":
        raise NotImplementedError("restart not implemented - try ctrl-c")

if __name__ == "__main__":
    sys.exit(main())
