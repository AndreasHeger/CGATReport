import os, re
from SphinxReport.Component import *
from SphinxReport import Config

class RSTPlugin(Component):
    '''collect rst text. 

    This plugin looks for image/figure directives in
    literal text output and changes their path so that
    they are valid within sphinx.

    images: path relative to rst directory

    links: path relative to html content
    
    '''

    capabilities = ['collect']

    # include white spaces at the end for length-neutral substitution
    rx_img = re.compile( "\.\. (image|figure):: ([^ |+,:]+[ ]*)")

    # external link targets:
    # .. _link: target
    rx_link = re.compile( "\.\. _([^ |+,:]+)\s*:\s*([^ |+,:]+)[ ]*")

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)

    def collect( self,
                 blocks,
                 template_name, 
                 outdir, 
                 rstdir,
                 builddir,
                 srcdir,
                 content,
                 display_options,
                 linked_codename,
                 tracker_id):
        '''collect rst output from result blocks.
        
        '''
        map_figure2text = {}

        def replace_and_pad( s, old, new ):
            '''replace old with new in s such that length of
            new+spaces is at least that of old+spaces.

            There needs to be enough space for padding. 
            '''
            
            oldlen = len(old)
            newlen = len(new)
            new = new + " " * (oldlen - newlen)
            n = s.replace( old, new)
            return n

        for xblocks in blocks:
            for block in xblocks:
                if not hasattr( block, "text" ): continue
                lines = block.text.split("\n")
                n = []
                for l in lines:
                    ll = l

                    for x in self.rx_img.finditer( ll ):
                        directive, filename = x.groups()
                        relpath = os.path.relpath( filename.strip(), os.path.abspath(rstdir))
                        newpath = re.sub("\\\\", "/", relpath )
                        l = replace_and_pad(l, filename, newpath )
                    

                    for x in self.rx_link.finditer( ll ):
                        directive, filename = x.groups()
                        newpath = re.sub("\\\\", "/", os.path.abspath( filename.strip()) )
                        # pad with spaces to keep table alignment
                        l = replace_and_pad(l, filename, newpath )

                    n.append( l )
                block.text = "\n".join( n )

        return map_figure2text
