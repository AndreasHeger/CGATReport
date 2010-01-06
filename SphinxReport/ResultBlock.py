import types, re, string

class ResultBlock:
    """Result of :class:``Renderer``

    A ResultBlock is a container of an :class:``Renderer`` result. It contains
    text (:attr:`text`) and a title (:attr:`title`).

    Blocks will be arranged according to the :term: `layout`
    option to the ``report`` directive.

    A result Block is recursive.
    """


    def __init__( self, text, title ):
        assert type(text) in types.StringTypes, "created ResultBlock without txt, but %s" % str(text)
        assert type(title) in types.StringTypes, "created ResultBlock without txt, but %s" % str(title)
        assert title != None
        assert text != None
        self.text = text
        self.title = title

    def _getWidth( self, txt ):
        """return the width of the block."""
        if txt == None: return 0
        return max( [len(x) for x in txt.split("\n")] )

    def _getHeight( self, txt ):
        """return the width of the block."""
        if txt == None: return 0
        return len( txt.split("\n"))

    def getWidth( self ):  return max( self._getWidth( self.text), self._getWidth( self.title) )
    def getHeight( self ): return max( self._getHeight( self.text), self._getHeight( self.title) )
    def getTextWidth( self ): return self._getWidth( self.text )
    def getTextHeight( self ): return self._getHeight( self.text )
    def getTitleWidth( self ): return self._getWidth( self.title )
    def getTitleHeight( self ): return self._getHeight( self.title )
    def updatePlaceholders( self, map_old2new ):
        '''apply map_old2new to placeholders.'''
        patterns = re.findall( "#\$[^$#]+\$#", self.text )
        for pattern in patterns:
            if pattern in map_old2new:
                self.text = self.text.replace( pattern,
                                               map_old2new[pattern] )
        if len(patterns) == 0:
            self.text = map_old2new["default-prefix"] +\
                self.text +\
                map_old2new["default-suffix"]

    def updateTitle( self, title, mode="prefix" ):
        if not self.title: 
            self.title = title
        elif mode == "prefix":
            self.title = "/".join( (title,self.title))
        elif mode == "suffix":
            self.title = "/".join( (self.title,title))
        else:
            self.title = title
    def __str__(self):
        return "\n\n".join( (self.title, self.text) )

class EmptyResultBlock(ResultBlock):
    '''place-holder for empty results.'''
    def __init__( self, title ):
        ResultBlock.__init__( self, "no data", title )

class ResultBlocks(object):
    '''
    '''
    __slots__=["_data", "title"]
    def __init__(self, block = None, title = None ):
        object.__setattr__( self, "_data", [])
        object.__setattr__( self, "title", title)
        if block: self._data.append( block )
    def __iter__(self):
        return self._data.__iter__()
    def __getitem__(self, key):
        return self._data.__getitem__(key)
    def __len__(self):
        return self._data.__len__()
    def __str__(self):
        return "\n".join( 
            ["##### %s #########\n" % self.title] +\
                [str(x) for x in self._data ])
    def updatePlaceholders( self, map_old2new ):
        '''recursively apply lines in text.'''
        for block in self._data:
            block.updatePlaceholders( map_old2new )
    def updateTitle( self, title, mode="prefix" ):
        '''update title with *title*.

        *mode* can be either ``prefix``, ``suffix``
        or ``replace``.
        '''
        for block in self._data:
            block.updateTitle( title, mode )
    def __getattr__(self, name):
        return getattr(self._data, name)
    def __setattr__(self, name, value):
        setattr(self._data, name, value) 

        
