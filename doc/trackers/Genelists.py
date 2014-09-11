from CGATReport.Tracker import *
#from CGATReportGeneLists.Tracker import *


class SimpleExampleData(Tracker):

    """Simple Example Data.
    """

    tracks = ["bicycle", "car"]

    def __call__(self, track, slice=None):
        if track == "car":
            return odict((("wheels", 4), ("max passengers", 5)))
        elif track == "bicycle":
            return odict((("wheels", 2), ("max passengers", 1)))


class DifferentialHead(TrackerSQL):

    def __call__(self, track):

        statement = "SELECT * FROM differential LIMIT 10"
        return self.getAll(statement)


class GeneListHead(TrackerSQL):

    def __call__(self, track):

        statement = "SELECT gene_id FROM Promoters_with_ar LIMIT 10"
        return {'gene_id': self.getValues(statement)}


class SimpleOverlap(TrackerMultipleLists):

    statements = {"AR": "SELECT gene_id FROM Promoters_with_ar",
                  "ERG": "SELECT gene_id FROM Promoters_with_erg",
                  "background": "SELECT gene_id FROM all_genes"}


class OverlapTracker(TrackerMultipleLists):
    pattern = "(.+)_with_.+"
    slices = ["logFC < 0", "logFC > 0"]

    # Note that the column names in the lists must match
    ListA = '''SELECT id as gene_id
                   FROM differential
                   WHERE FDR < 0.05 AND %(slice)s '''

    ListB = '''SELECT gene_id
    FROM %(track)s_with_ar as ar,
    differential as diff
    WHERE ar.gene_id = diff.id'''

    ListC = '''SELECT gene_id
                   FROM %(track)s_with_erg as erg,
                         differential as diff
                   WHERE erg.gene_id = diff.id'''

    background = '''SELECT id AS gene_id FROM differential'''

    # we also need to add backround to the labels
    labels = ["Differentially Expressed",
              "Bound by AR",
              "Bound by ERG",
              "background"]
