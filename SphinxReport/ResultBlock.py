import types, re, string

class ResultBlock:
    """Result of :class:``Renderer``

    A ResultBlock is a container of an :class:``Renderer`` result. It contains
    text (:attr:`mText`) and an optional title (:attr:`mTitle`).

    Blocks will be arranged according to the :term: `layout`
    option to the ``report`` directive.

    """
    def __init__( self, text, title = "" ):
        assert type(text) in types.StringTypes, "created ResultBlock without txt, but %s" % str(text)
        self.mText = text
        self.mTitle = title

    def _getWidth( self, txt ):
        """return the width of the block."""
        if txt == None: return 0
        return max( [len(x) for x in txt.split("\n")] )

    def _getHeight( self, txt ):
        """return the width of the block."""
        if txt == None: return 0
        return len( txt.split("\n"))

    def getWidth( self ):  return max( self._getWidth( self.mText), self._getWidth( self.mTitle) )
    def getHeight( self ): return max( self._getHeight( self.mText), self._getHeight( self.mTitle) )
    def getTextWidth( self ): return self._getWidth( self.mText )
    def getTextHeight( self ): return self._getHeight( self.mText )
    def getTitleWidth( self ): return self._getWidth( self.mTitle )
    def getTitleHeight( self ): return self._getHeight( self.mTitle )

    def __str__(self):
        return "\n\n".join( (self.mTitle, self.mText) )
