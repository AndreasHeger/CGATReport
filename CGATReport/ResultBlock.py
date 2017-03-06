from __future__ import unicode_literals

import re
import itertools
from six import string_types


class ResultBlock(object):

    """Result of:class:``Renderer``

    A ResultBlock is a container of an:class:``Renderer`` result. It
    contains text (:attr:`text`) and a title (:attr:`title`).

    Blocks will be arranged according to the:term: `layout`
    option to the ``report`` directive.

    Each block might contain a pre-amble or post-amble that
    will be added to text.

    """

    def __init__(self, text, title="", preamble="", postamble=""):
        assert isinstance(
            text, string_types), \
            "created ResultBlock without text, but %s" % str(type(text))
        if title:
            assert isinstance(
                title, string_types), \
                "created ResultBlock without title, but %s" % str(title)
        assert text is not None
        self.text = text
        self.title = title
        self.preamble = preamble
        self.postamble = postamble

    def _getWidth(self, txt):
        """return the width of the block."""
        if txt is None:
            return 0
        return max([len(x) for x in txt.split("\n")])

    def _getHeight(self, txt):
        """return the width of the block."""
        if txt is None:
            return 0
        return len(txt.split("\n"))

    def getWidth(self):
        return max(self._getWidth(self.text),
                   self._getWidth(self.title),
                   self._getWidth(self.preamble),
                   self._getWidth(self.postamble))

    def getHeight(self):
        return max(self._getHeight(self.text),
                   self._getHeight(self.title),
                   self._getHeight(self.preamble),
                   self._getHeight(self.postamble))

    def getTextWidth(self):
        return self._getWidth(self.text)

    def getTextHeight(self):
        return self._getHeight(self.preamble) +\
            self._getHeight(self.text) +\
            self._getHeight(self.postamble)

    def getTitleWidth(self):
        return self._getWidth(self.title)

    def getTitleHeight(self):
        return self._getHeight(self.title)

    def updatePlaceholders(self, map_old2new):
        '''apply map_old2new to placeholders.'''
        patterns = re.findall("#\$[^$#]+\$#", self.text)
        for pattern in patterns:
            if pattern in map_old2new:
                self.text = self.text.replace(pattern,
                                              map_old2new[pattern])
        if len(patterns) == 0:
            self.text = map_old2new.get("default-prefix", "") +\
                self.text +\
                map_old2new.get("default-suffix", "")

    def updateTitle(self, title, mode="prefix"):
        if not self.title:
            self.title = title
        elif mode == "prefix":
            self.title = "/".join((title, self.title))
        elif mode == "suffix":
            self.title = "/".join((self.title, title))
        else:
            self.title = title
        # normalize titel
        parts = self.title.split("/")
        # make unique
        self.title = "/".join([key for key, _ in itertools.groupby(parts)])

    def clearPostamble(self):
        self.postamble = ""

    def clearPreamble(self):
        self.preamble = ""

    def __unicode__(self):
        a = [self.title,
             self.preamble,
             self.text,
             self.postamble]
        return "\n\n".join((self.title,
                            self.preamble,
                            self.text,
                            self.postamble))

    def __str__(self):
        a = [self.title,
             self.preamble,
             self.text,
             self.postamble]
        return "\n\n".join((self.title,
                            self.preamble,
                            self.text,
                            self.postamble))


class EmptyResultBlock(ResultBlock):

    '''place-holder for empty results.'''

    def __init__(self, title):
        ResultBlock.__init__(self, "no data", title)


class ResultBlocks(object):

    '''A collection of:class:`ResultBlock`.

    This class is recursive.
    '''
    __slots__ = ["_data", "title"]

    def __init__(self, block=None, title=None):

        self.title = title
        if block:
            if isinstance(block, ResultBlock):
                self._data = [block]
            elif isinstance(block, list) and isinstance(block[0], ResultBlock):
                self._data = block
            else:
                raise ValueError("expected ResultBlock or list of ResultBlock, but got {}".format(
                    type(block)))
        else:
            self._data = []

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __len__(self):
        return self._data.__len__()

    def __str__(self):
        return "\n".join(
            ["##### %s #########\n" % self.title] +
            [str(x) for x in self._data])

    def updatePlaceholders(self, map_old2new):
        '''recursively apply lines in text.'''
        for block in self._data:
            block.updatePlaceholders(map_old2new)

    def updateTitle(self, title, mode="prefix"):
        '''update title with *title*.

        *mode* can be either ``prefix``, ``suffix``
        or ``replace``.
        '''
        for block in self._data:
            block.updateTitle(title, mode)

    def append(self, value):
        if not isinstance(value, ResultBlock):
            raise ValueError("appending not a ResultBlock: {}".format(
                type(value)))
        self._data.append(value)

    def extend(self, values):
        if not isinstance(values, ResultBlocks):
            raise ValueError("extending is not a ResultBlocks: {}".format(
                type(values)))
        self._data.extend(values)

    def clearPostamble(self):
        for block in self._data:
            block.clearPostamble()

    def clearPreamble(self):
        for block in self._data:
            block.clearPostamble()


def flat_iterator(blocks):
    stack = [("", blocks)]
    while stack:
        path, e = stack[-1]
        for k, v in list(e.items()):
            if isinstance(v, dict):
                stack.append((path + k, v))
            else:
                yield path + k, v
        stack.remove((path, e))
