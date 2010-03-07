import os, re
from SphinxReport.Component import *
from SphinxReport import Config

class HTMLPlugin(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)

    def collect( self,
                 blocks,
                 template_name, 
                 outdir, 
                 linkdir, 
                 content,
                 display_options,
                 linked_codename,
                 tracker_id):
        '''collect html output from result blocks.

        HTML output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}
        extension = "html"
        
        for xblocks in blocks:
            for block in xblocks:
                if not hasattr( block, "html" ): continue

                outname = "%s_%s" % (template_name, block.title)
                outputpath = os.path.join(outdir, '%s.%s' % (outname, extension))

                # save to file
                outf = open( outputpath, "w")
                outf.write( block.html )
                outf.close()

                path = re.sub( "\\\\", "/", os.path.join( linkdir, outname ) )
                link = path + "." + extension

                rst_output = "%(link)s" % locals()

                map_figure2text[ "#$html %s$#" % block.title] = rst_output

        return map_figure2text
