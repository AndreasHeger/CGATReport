from CGATReportPlugins.Transformer import Transformer
from collections import OrderedDict as odict
from docutils.parsers.rst import directives
from CGATReport import DataTree, Utils
from CGATReport.DataTree import path2str
import itertools
import math
import scipy.stats


class TransformerHypergeometric(Transformer):

    '''Takes in lists of items (genes) and computes a hypergeometric p
    value and fold enrichment on the overlap between the lists.

    Takes bottom level of the data tree, which is expects to be a
    dictionary of lists, one of which should be named background. It
    will check if all the items in the other lists are also in the
    background list.

    If the dictionary contains more than 2 lists in addition to
    background, all pairwise overlaps are calculated.

    '''

    nlevels = -1

    def transform(self, data):

        # check if data is melted:
        if len(data.columns) != 1:
            raise ValueError(
                'transformer requires dataframe with'
                'a single column, got %s' % data.columns)
        column = data.columns[0]

        # iterate over lowest levels to build a dictionary of
        # sets
        genesets = {}
        nlevels = Utils.getDataFrameLevels(data)
        for key, group in data.groupby(level=range(nlevels)):
            genesets[path2str(key)] = set(group[column])

        keys = genesets.keys()

        background = None
        foreground = []
        for key in keys:
            if "background" in key:
                background = genesets[key]
            else:
                foreground.append(key)

        if len(keys) < 3 or background is None:
            raise ValueError(
                "Expected at least 3 lists, with one called background, "
                "instead got %i lists called %s" %
                (len(keys), ", ".join(keys)))

        missing = {
            y: [str(x) for x in genesets[y]
                if x not in background] for y in foreground}

        if any([len(missing[x]) > 0 for x in missing]):
            missing_items = "\n\t".join(
                ["%s:\t%s" % (x, ",".join(missing[x])) for x in missing])
            raise ValueError(
                "Found items in lists not in background. "
                "Missing items:\n\t %s" % missing_items)

        M = len(set(background))
        if len(keys) == 2:

            n = len(set(genesets[keys[1]]))
            N = len(set(genesets[keys[0]]))
            x = len(set(genesets[keys[0]]) & set(genesets[keys[1]]))

            p = scipy.stats.hypergeom.sf(x, M, n, N)

            fc = ((x + 0.0) / N) / ((n + 0.0) / M)

            values = [("Enrichment", fc),
                      ("P-value", p)]
        else:
            enrichments = []
            pvals = []
            As = []
            Bs = []
            for a, b in itertools.combinations(keys, 2):
                N = len(set(genesets[a]))
                n = len(set(genesets[b]))
                x = len(set(genesets[a]) & set(genesets[b]))

                p = scipy.stats.hypergeom.sf(x, M, n, N)

                fc = ((x + 0.0) / N) / ((n + 0.0) / M)

                As.append(a)
                Bs.append(b)
                pvals.append(p)
                enrichments.append(fc)

            values = [("ListA", As),
                      ("ListB", Bs),
                      ("Enrichment", enrichments),
                      ("P-value", pvals)]

        return DataTree.listAsDataFrame(values, values_are_rows=True)


class TransformerOddsRatio(Transformer):

    ''' Takes in lists of items (genes) and computes a hypergeometric p value and fold enrichment
    on the overlap between the lists.

    Takes bottom level of the data tree, which is expects to be a dictionary of lists, one of which
    should be named background. It will check if all the items in the other lists are also in
    the background list.

    If the dictionary contains more than 2 lists in addition to background, all pairwise overlaps
    are calculated. '''

    nlevels = 1

    def transform(self, data):

        keys = data.keys()
        if len(keys) < 3 or "background" not in data.keys():
            raise ValueError("Expected at least 3 lists, with one called background, instead got %i lists called %s" % (
                len(keys), ", ".join(keys)))

        keys = [x for x in keys if x != "background"]

        missing = {
            y: [str(x) for x in data[y] if x not in data["background"]] for y in keys}

        if any([len(missing[x]) > 0 for x in missing]):

            missing_items = "\n\t".join(
                ["%s:\t%s" % (x, ",".join(missing[x])) for x in missing])

            raise ValueError(
                "Found items in lists not in background. Missing items:\n\t %s" % missing_items)

        if len(keys) == 2:

            a = len(set(data[keys[0]]) & set(data[keys[1]]))
            b = len(set(data[keys[0]]) - set(data[keys[1]]))
            c = len(set(data[keys[1]]) - set(data[keys[0]]))
            d = len(
                set(data["background"]) - set(data[keys[0]]) - set(data[keys[1]]))

            table = [[a, b], [c, d]]

            OR, p = fisher_exact(table)

            sigma = math.sqrt((1.0 / a) + (1.0 / b) + (1.0 / c) + (1.0 / d))

            CI95_hi = OR * math.exp(1.96 * sigma)
            CI95_low = OR * math.exp(-1.96 * sigma)

            return odict([("OddRatio", OR),
                          ("CI95_hi", CI95_hi),
                          ("CI95_low", CI95_low),
                          ("P-value", p)])

        else:
            ORs = []
            pvals = []
            CIhis = []
            CIlos = []
            As = []
            Bs = []
            for x, z in itertools.combinations(keys, 2):

                a = len(set(data[x]) & set(data[z]))
                b = len(set(data[x]) - set(data[z]))
                c = len(set(data[z]) - set(data[x]))
                d = len(set(data["background"]) - set(data[x]) - set(data[z]))

                table = [[a, b], [c, d]]

                OR, p = fisher_exact(table)

                sigma = math.sqrt(
                    (1.0 / a) + (1.0 / b) + (1.0 / c) + (1.0 / d))

                CI95_hi = OR * math.exp(1.96 * sigma)
                CI95_low = OR * math.exp(-1.96 * sigma)

                As.append(x)
                Bs.append(z)
                pvals.append(p)
                ORs.append(OR)
                CIhis.append(CI95_hi)
                CIlos.append(CI95_low)

            return odict([("ListA", As),
                          ("ListB", Bs),
                          ("OddsRatio", ORs),
                          ("CI95_hi", CIhis),
                          ("CI95_low", CIlos),
                          ("P-value", pvals)])


class TransformerVenn(Transformer):
    '''Takes dictionarys of lists and transforms the data into the correct
    format for use with the venn renderer. If the dictionary contains
    a background entry and all other entries are subsets of the
    background, then it is removed, unless the keep-background options
    is specified.

    e.g.

    This:                           Becomes:
    a/x/[1,2,3]                     a/01/1
    a/y/[2,3,4]                     a/10/1
    a/background/[1,2,3,4,5]        a/11/2
    b/x/[5,6,7]                     b/01/1
    b/y/[6,7,8]                     b/10/1
                                    b/11/2

    Currently handles 2 or 3 way overlaps

    '''

    nlevels = -1

    options = Transformer.options + (
        ('keep-background', directives.flag),)

    background = False

    prune_dataframe = False

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.background = "keep-background" in kwargs

    def transform(self, data):

        # check if data is melted:
        if len(data.columns) != 1:
            raise ValueError(
                'transformer requires dataframe with '
                'a single column, got %s' % data.columns)
        column = data.columns[0]
        # iterate over lowest levels to build a dictionary of
        # sets
        genesets = {}
        nlevels = Utils.getDataFrameLevels(data)
        for key, group in data.groupby(level=range(nlevels)):
            if "background" in key and not self.background:
                continue
            genesets[key] = set(group[column])
            
        values = []
        if len(genesets) == 2:
            a = set(genesets[genesets.keys()[0]])
            b = set(genesets[genesets.keys()[1]])

            values.append(("10", len(a - b)))
            values.append(("01", len(b - a)))
            values.append(("11", len(a & b)))
            values.append(("labels", map(path2str, genesets.keys())))
        elif len(genesets) == 3:
            a = set(genesets[genesets.keys()[0]])
            b = set(genesets[genesets.keys()[1]])
            c = set(genesets[genesets.keys()[2]])

            values.append(("100", len(a - b - c)))
            values.append(("010", len(b - a - c)))
            values.append(("001", len(c - a - b)))
            values.append(("110", len((a & b) - c)))
            values.append(("101", len((a & c) - b)))
            values.append(("011", len((b & c) - a)))
            values.append(("111", len((a & b) & c)))
            values.append(("labels", map(path2str, genesets.keys())))
        else:
            raise ValueError(
                "Can currently only cope with 2 or 3 way intersections")

        return DataTree.listAsDataFrame(values)


class TransformerMultiTest(Transformer):
    '''This transformer performs multiple testing correction.

    A multiple testing is applied to P-Values in a column called
    *P-value* (can be changed using the ``p-value`` option).

    The original data frame is returned with an added ``P-adjust``
    column. The default method for correction is BH, but other R style
    correction methods can be specified with ``adj-method`` option.

    P-values are adjusted overall.
    '''

    options = Transformer.options + (
        ('adj-method', directives.unchanged),
        ('p-value', directives.unchanged),)

    # group everything together
    nlevels = 0

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.method = kwargs.get("adj-method", "BH")
        self.pval = kwargs.get("p-value", "P-value")

    def transform(self, data):

        from rpy2.robjects import r as R

        padj = R["p.adjust"](data[self.pval],
                             method=self.method)

        data["P-adjust"] = padj
        return data
