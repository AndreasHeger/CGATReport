from CGATReport.Tracker import TrackerSQL


class ExpressionLevels(TrackerSQL):
    """Expression level measurements."""

    def __call__(self, track):
        statement = """SELECT e1.expression AS experiment1,
                              e2.expression AS experiment2,
                              e1.function as gene_function
                       FROM experiment1_data as e1,
                                 experiment2_data as e2
                       WHERE e1.gene_id = e2.gene_id
                    """

        return self.getDataFrame(statement)

