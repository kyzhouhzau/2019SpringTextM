#!/usr/bin/python
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

#================
class Mention(object):

    def __init__(self, id, sec, t, spans, string):
        self.id = id
        self.sec = sec
        self.t = t
        self.spans = spans      # a list of (beg, end) integers
        self.string = string

    @classmethod
    def from_lxml(cls, x):
        """Given an object that is an element in the result of an xpath search,
        obtains the mention elements from it
        and create and return a Mention object

        Input:
        x: XML mention object
        """
        sec_id = x.get("section")
        id = x.get("id").replace("M", "T")
        t = x.get("type")
        beg = x.get("start")
        l = x.get("len")
        string = x.get("str")
        # keep general: allow discontinuous mentions (hoping they break at space)
        # TAC format: start="618,640" len="8,8" str="Suicidal Ideation"
        # BRAT format: 618 626;640 648	Suicidal Ideation
        beg_l = beg.split(sep=",")
        l_l = l.split(sep=",")
        span_l = [ (int(b), int(b) + int(l_l[i])) for i, b in enumerate(beg_l) ]
        return cls(id, sec_id, t, span_l, string)

    def sprint_spans(self, spans, offset=0):
        return ";".join( [ "{} {}".format(b+offset, e+offset) for b, e in spans ] )

    def sprint(self, offset=0):
        "T1	Protein 889 901	NF-kappaBp65"
        return "{}\t{} {}\t{}".format(self.id, self.t, self.sprint_spans(self.spans, offset=offset), self.string)

    def __repr__(self):
        "T1	Protein 889 901	NF-kappaBp65"
        return "<Mention {} {} {} {}>".format(self.id, self.t, self.sprint_spans(self.spans), self.string)

#================
class Relation(object):

    def __init__(self, id, t, args):
        self.id = id
        self.t = t
        self.args = args

    @classmethod
    def from_lxml(cls, x):
        """Given an object that is an element in the result of an xpath search,
        obtains the relation elements from it
        and create and return a Relation object
        <Relation id="RL1" type="Effect" arg1="M5" arg2="M4" />

        Input:
        x: XML mention object
        """
        id = x.get("id").replace("RL", "R")
        t = x.get("type")
        arg1 = x.get("arg1").replace("M", "T")
        arg2 = x.get("arg2").replace("M", "T")
        return cls(id, t, (arg1, arg2))

    def sprint(self, offset=0):
        "R1	SUBJ Arg1:T3 Arg2:T2"
        return "{}\t{} {}".format(self.id, self.t, " ".join([ "Arg{}:{}".format(i, a) for i, a in enumerate(self.args) ]))
