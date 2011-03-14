import os, re
from SphinxReport.Component import *
from SphinxReport import Config

class RSTPlugin(Component):
    '''collect rst text. 

    This plugin looks for image/figure directives in
    literal text output and changes their path.
    '''

    capabilities = ['collect']

    rx = re.compile( "\.\. (image|figure):: (\S+)")

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)

    def collect( self,
                 blocks,
                 template_name, 
                 outdir, 
                 rstdir,
                 rst2rootdir, 
                 rst2builddir,
                 content,
                 display_options,
                 linked_codename,
                 tracker_id):
        '''collect html output from result blocks.

        HTML output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}

        for xblocks in blocks:
            for block in xblocks:
                if not hasattr( block, "text" ): continue
                
                lines = block.text.split("\n")
                n = []
                for l in lines:
                    x = self.rx.search( l )
                    if x:
                        directive, filename = x.groups()
                        relpath = os.path.relpath( filename, os.path.abspath(rstdir))
                        imagepath = re.sub("\\\\", "/", relpath )
                        l = re.sub( filename, imagepath, l )
                    n.append( l )
                block.text = "\n".join( n )

        return map_figure2text
