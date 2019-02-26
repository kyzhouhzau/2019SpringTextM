#!/usr/bin/python
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import logging

#================
class Token(object):
    """Processing and representation of a token.

    string: the text contents as a raw string
    span: (begin, end) offsets
    """

    def __init__(self, string, span): # , sentence, text):
        self.string = string
        self.span = span
        self.mentions = []
        # self.sentence = sentence
        # self.text = text
        return

    def __len__(self):
        return len(self.string)

    def __iter__(self):
        return (e for e in self.string)

    def __repr__(self):
        return "<Token '{}':{}-{}>".format(self.string, *self.span)

    def sprint(self, convert_eol=False, replace_eol_with=' '):
        """Printed representation of a token: by default, its string.
        If convert_eol is True,  replaces \\n characters with the value of replace_eol_with."""
        logging.debug("Printing {}".format(self))
        if convert_eol:
            return self.string.replace("\n", replace_eol_with)
        else:
            return self.string

    def register_mention(self, m, is_first=False, is_last=False):
        logging.debug("register_mention: {}-{} {}".format(is_first, is_last, m))
        self.mentions.append((m, is_first, is_last))
        return




