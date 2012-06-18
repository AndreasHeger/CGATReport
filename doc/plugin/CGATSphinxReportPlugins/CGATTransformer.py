from SphinxReportPlugins.Transformer import Transformer

class TransformerCount( Transformer ):
    '''Count the number of items on the top level of 
    the hierarchy.
    '''
    
    nlevels = 0

    def transform(self, data, path):
        for v in data.keys():
            data[v] = len( data[v] )
        return data

