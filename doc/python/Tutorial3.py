from SphinxReport.DataTypes import *
from SphinxReport.Tracker import *

import os

class WordCounter(Tracker):
    """Counting word size."""
    
    def getTracks( self, subset = None ):
        return ( "all", ".py", ".rst" )

    def __call__(self, track, slice = None ):
        word_sizes = []
        
        if track == "all" or track == None:
            tracks = [ ".py", ".rst" ]
        else:
            tracks = [track]
        
        for root, dirs, files in os.walk('.'):
            for f in files:
                fn, ext = os.path.splitext( f )
                if ext not in tracks: continue
                infile = open(os.path.join( root, f),"r")
                words = re.split("\s+", "".join(infile.readlines()))
                word_sizes.extend( [ len(word) for word in words ] )
                infile.close()
                    
        return { "word sizes" : word_sizes }

class WordCounterWithSlices(Tracker):
    """Counting word size."""
    
    def getTracks( self, subset = None ):
        return ( "all", ".py", ".rst" )

    def getSlices( self, subset = None ):
        return ( "all", "vocals", "consonants")

    def __call__(self, track, slice = None ):
        word_sizes = []
        
        if track == "all" or track == None:
            tracks = [ ".py", ".rst" ]
        else:
            tracks = [track]
        
        if slice == "all" or slice == None:
            test_f = lambda x: True
        elif slice == "vocals":
            test_f = lambda x: x[0].upper() in "AEIOU"
        elif slice == "consonants":
            test_f = lambda x: x[0].upper() not in "BCDFGHJKLMNPQRSTVWXYZ"

        for root, dirs, files in os.walk('.'):
            for f in files:
                fn, ext = os.path.splitext( f )
                if ext not in tracks: continue
                infile = open(os.path.join( root, f),"r")
                words = [ w for w in re.split("\s+", "".join(infile.readlines())) if len(w) > 0]
                word_sizes.extend( [ len(w) for w in words if test_f(w)] )
                infile.close()
                    
        return { "word sizes" : word_sizes }
