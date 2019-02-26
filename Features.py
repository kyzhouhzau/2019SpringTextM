#!/usr/bin/python
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
import pdb
import logging

#================
class FeatureParser(object):
    """ Given a feature specification, returns an instantiated feature object with this specification."""

    def __init__(self, spec):
        """
        Input:
        spec (a string) containing
            1. a feature name 2. optionally, a colon-separated list of arguments.
            Example: "TokenDict:msh:msh-diso-1.dic"
            The feature name must be a class name, the arguments are passed to the class creator."""
        self.spec = spec
        l = spec.split(":")
        cls = l[0]
        args = l[1:]
        logging.info("Parsing feature '{}' into '{}' + {}".format(self.spec, cls, args))

        cls_obj = getattr(sys.modules[__name__], cls, None)
        logging.info("Actual class is {}".format(cls_obj))
        if cls_obj is None:
            raise NameError ("Undefined feature name: '{}', must be a class name".format(cls))
        else:
            try:
                f = cls_obj(*args)
            except:
                raise NameError ("Undefined feature name: '{}', must be a class name".format(cls))
            else:
                if getattr(f, "feature"):
                    self.f = f
                else:
                    raise ValueError ("Unsuitable feature name: '{}', must have a 'feature' method".format(cls))
        return


#================
class TokenDict(object):
    """Dictionary of tokens."""

    def __init__(self, name, file, lc=False, absent="O"):
        """Given a FILE that contains one word per line
        and the NAME of a category,
        creates a dict (= hash) that assigns this category to each word in the file
        and puts it into self.tokens.

        Example call: msh_dic = self.read("msh-diso-1.dic", "diso1")
        Example output: { "viral": "diso1", "virus": "diso1", ... }
        Example call: nci_dic = read_dict("msh-diso-1.dic", "diso2")
        Example output dictionary: { "acanthosis": "diso2", ... }
    """
        self.name = name
        self.file = file
        self.lc = (True if lc == "True" else lc is True)
        self.tokens = {}
        self.absent = absent
        self.load_tokens()
        return

    def load_tokens(self):
        with open(self.file, "r") as inf:
            # remove \n at the end of each word
            if self.lc:
                self.tokens = { w[:-1].casefold():self.name for w in inf.readlines() }
            else:
                self.tokens = { w[:-1]:self.name for w in inf.readlines() }
            # print(self.tokens)
            # pdb.set_trace()
		
        return

    def __len__(self):
        return len(self.tokens)

    def __contains__(self, key):
        if len(key)>3:
            return key in self.tokens

    def __geitem__(self, key):
        return self.tokens[key]

    def __repr__(self):
        return "<TokenDict '{}' for file '{}' with {} tokens>".format(self.name, self.file, len(self))

    def feature_named(self, token):
        if token in self:
            return self.name
        else:
            return self.absent

    def feature_binary(self, token):
        return token in self

    def feature(self, token):   # generic method, must be present
        if self.lc:
            token = token.casefold()
        logging.info("{} --- Computing feature for token '{}'.".format(self, token))
        return self.feature_named(token)

#================
if __name__ == '__main__':
    # testing: must have files nci-diso-1.dic and msh-diso-1.dic in current directory
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # f_msh = TokenDict("diso_msh", "msh-diso-1.dic")
    f_msh = FeatureParser("TokenDict:dis:dis-DISO-2.dic").f
    # f_msh = [fp.feature_named(t) for t in ["the", "virus", "of", "acanthosis"]]
    print(f_msh)
    w = "virus"
    print("Is '{}' in the dictionary?: {}".format(w, w in f_msh))
    w = "acanthosis"
    print("Is '{}' in the dictionary?: {}".format(w, w in f_msh))
    f = [f_msh.feature_named(t) for t in ["the", "virus", "of", "acanthosis"]]
    print("Features: {}".format(f))

    # # f_nci = TokenDict("diso_nci", "nci-diso-1.dic")
    # f_nci = FeatureParser("TokenDict:nature:nature-source-3.dic").f
    # print(f_nci)
    # w = "virus"
    # print("Is '{}' in the dictionary?: {}".format(w, w in f_nci))
    # w = "acanthosis"
    # print("Is '{}' in the dictionary?: {}".format(w, w in f_nci))
    # f = [f_nci.feature_named(t) for t in ["the", "virus", "of", "acanthosis"]]
    # print("Features: {}".format(f))

    f_bogus = FeatureParser("bogus:random_arg").f
