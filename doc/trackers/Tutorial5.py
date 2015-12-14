from CGATReport.Tracker import TrackerSQL


class ExpressionLevel(TrackerSQL):

    """Expression level measurements."""
    pattern = "(.*)_data$"

    def __call__(self, track):
        statement = "SELECT expression FROM %s_data" % track
        data = self.getValues(statement)
        return {"expression": data}


class ExpressionLevelWithSlices(ExpressionLevel):

    """Expression level measurements."""

    slices = ("housekeeping", "regulation")

    def __call__(self, track, slice):
        if not slice:
            where = ""
        else:
            where = "WHERE function = '%s'" % slice
        statement = "SELECT expression FROM %s_data %s" % (track, where)
        data = self.getValues(statement)
        return {"expression": data}
