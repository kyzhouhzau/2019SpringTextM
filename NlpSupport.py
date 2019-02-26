#!/usr/bin/python
# -*- coding: utf-8 -*-
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

"""
NLP Support:
Generic class, then one subclass per language or processing variant.
"""
"""
    Copyright (c) 2017 LIMSI CNRS
    All rights reserved.
    Pierre Zweigenbaum, LIMSI, CNRS, Université Paris-Saclay <pz@limsi.fr>
    Thomas Lavergne, LIMSI, CNRS, Univ. Paris-Sud, Université Paris-Saclay <lavergne@limsi.fr>
"""

# http://stackoverflow.com/questions/491921/unicode-utf8-reading-and-writing-to-files-in-python
import codecs
import os
import sys
import unicodedata
import re
import logging

import nltk
# choose nltk_data location for my laptop: update as needed for your machine
nltk.data.path = ( ['nltk_data'] if os.path.exists('nltk_data') else  ['/vol/datailes/tools/nlp/nltk_data/2016'] )
# from nltk.tokenize import WordPunctTokenizer
# word_punct_tokenizer = WordPunctTokenizer()
import nltk.tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer, EnglishStemmer

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents(s):
    """Remove all diacritics from input string s"""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

#================
# NlpSupport
#================

class NlpSupport():
    """
    Encapsulate methods for language-dependent tokenization, stemming, etc.
    """

    def tokenize_normalize2(self, s):
        return [
            self.stemmer.stem(strip_accents(tok)) # 4. remove diacritics, 5. stem
            for tok in [w.lower()   # 2. lower-case
                        for w in nltk.regexp_tokenize(s.strip(), self.TokenPattern2)] # 1. tokenize
            if tok not in self.lang_stopwords ] # 3. remove stopwords

    def tokenize_normalize(self, s):
        return [
            self.stemmer.stem(strip_accents(tok)) # 4. remove diacritics, 5. stem
            for tok in nltk.regexp_tokenize(s.strip().lower(), self.TokenPattern3) # 1. lower-case, 2. tokenize
            if tok not in self.lang_stopwords ] # 3. remove stopwords

    def tokenize_keep_hyphens_nostem(self, s):
        return [
            self.normalize_with_dict(strip_accents(tok)) # 4. remove diacritics, 5. normalize with dictionary
            for tok in nltk.regexp_tokenize(s.strip().lower(), self.TokenPatternHyphNoPunct3) # 1. lower-case, 2. tokenize
            if tok not in self.lang_stopwords ] # 3. remove stopwords

    def tokenize_keep_hyphens_nostem_keep_diacritics(self, s):
        return [
            self.normalize_with_dict(tok) # 4. normalize with dictionary
            for tok in nltk.regexp_tokenize(s.strip().lower(), self.TokenPatternHyphNoPunct3) # 1. lower-case, 2. tokenize
            if tok not in self.lang_stopwords ] # 3. remove stopwords

    #====
    # Spelling correction dictionary
    def read_normalization_dict(self, file):
        fh = codecs.open(file, "r", "utf-8")
        self.norm_dict = {}
        count_rx = re.compile(":\d+")
        while 1:
            l = fh.readline()
            # sys.stderr.write('  On line "{}"\n'.format(l))
            if l == "":
                break
            equivalents = re.sub(count_rx, "", l).split(sep=" ")
            normalized = equivalents[0]
            for i in range(1, len(equivalents)):
                self.norm_dict[equivalents[i]] = normalized
        fh.close()
        return self.norm_dict

    def normalize_with_dict(self, token):
        # norm_dict = (norm_dict if norm_dict else self.normalization_dict)
        return (self.norm_dict[token] if token in self.norm_dict else token)

    def tokenize_word_punct(self, s):
        return self.word_punct_tokenizer.tokenize(s)

    def tokenize_sent(self, s):
        return self.word_punct_tokenizer.tokenize(s)

#================
# NlpSupport: French
#================

class NlpSupportFrench(NlpSupport):
    """
    Encapsulate methods for French tokenization, stemming, etc.
    """

    def __init__ (self, ndf=None):
        logging.info("Providing language support for {}".format(type(self).__name__))
        self.lang_stopwords = set(stopwords.words('french') + [",", "d'", "l'", "(", ")"])
        for w in ['ait', 'a', 'b', 'c']: # hépatite A B C, AIT
            self.lang_stopwords.discard(w)

        self.stemmer = FrenchStemmer()
        self.norm_dict = {}

        # for python2
        self.TokenPattern2 = r'''(?x)    # set flag to allow verbose regexps
             ([A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w' # single-letter elided pronoun or determiner with final apostrophe
           | \w+(-\w+)*        # words with optional internal hyphens
           | \$?\d+(\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"'?():_`\|\n-]  # these are separate tokens; includes ], [, -
         '''
        # for python3
        self.TokenPatternHyph3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w' # single-letter elided pronoun or determiner with final apostrophe
           | \w+(?:-\w+)*        # words with optional internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"'?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')

        self.TokenPatternHyphNoPunct3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w' # single-letter elided pronoun or determiner with final apostrophe
           | \w+(?:-\w+)*        # words with optional internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
        #   | \.\.\.            # ellipsis
        #   | [][.,;"'?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')

        self.TokenPattern3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w' # single-letter elided pronoun or determiner with final apostrophe
        #   | \w+(?:-\w+)*        # words with optional internal hyphens
           | \w+        # words without internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"'?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')

        if ndf:
            logging.info("Reading the normalization dictionary from {}...".format(ndf))
            self.read_normalization_dict(ndf)
            # print_time(" done: ")

        # print_time(" done: ")


#================
# NlpSupport: English
#================

class NlpSupportEnglish(NlpSupport):
    """
    Encapsulate methods for English tokenization, stemming, etc.
    """

    def __init__ (self, ndf=None):
        logging.info("Providing language support for {}".format(type(self).__name__))
        self.lang_stopwords = set(stopwords.words('english') + [",", "(", ")"])
        for w in ['a', 'b', 'c']: # hepatitis A B C
            self.lang_stopwords.discard(w)

        self.stemmer = EnglishStemmer()
        # self.word_tokenizer = nltk.WordPunctTokenizer()
        # self.word_tokenizer = nltk.TreebankWordTokenizer()
        self.sent_tokenizer = nltk.PunktSentenceTokenizer()
        self.norm_dict = {}

        # for python2
        self.TokenPattern2 = r'''(?x)    # set flag to allow verbose regexps
             ([A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w+(-\w+)*        # words with optional internal hyphens
           | \$?\d+(\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"?():_`\|\n-]  # these are separate tokens; includes ], [, -
         '''
        # removed % French:
        # | \w' # single-letter elided pronoun or determiner with final apostrophe
        # ' from token separator
        # for python3
        self.TokenPatternHyph3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w+(?:-\w+)*        # words with optional internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')
        # removed % French:
        #           | \w' # single-letter elided pronoun or determiner with final apostrophe
        # ' from token separator

        self.TokenPatternHyphNoPunct3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
           | \w+(?:-\w+)*        # words with optional internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
        #   | \.\.\.            # ellipsis
        #   | [][.,;"?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')
        # removed % French:
        # | \w' # single-letter elided pronoun or determiner with final apostrophe
        # ' from token separator

        self.TokenPattern3 = re.compile(r'''(?x)    # set flag to allow verbose regexps
             (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
        #   | \w' # single-letter elided pronoun or determiner with final apostrophe
        #   | \w+(?:-\w+)*        # words with optional internal hyphens
           | \w+        # words without internal hyphens
           | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
           | \.\.\.            # ellipsis
           | [][.,;"?():_`\|\n-]  # these are separate tokens; includes ], [, -
         ''')
        # removed % French:
        # | \w' # single-letter elided pronoun or determiner with final apostrophe
        # ' from token separator

        self.TokenPatternTB = re.compile(r'''(?x)    # set flag to allow verbose regexps: ignores spaces and newlines
        (?:[A-Z]\.)+        # abbreviations, e.g. U.S.A.
        | \$?\d+(?:\.\d+)?%?  # currency and percentages, e.g. $12.40, 82%
        | '(?:s|nt)\b                      # 's, 'nt
        #     | \w+(?:-\w+)*        # words with optional internal hyphens
        | \w+        # words without internal hyphens (not good for xx-treated, xx-related, xx-controlled, xx-dose, etc.
        | \.\.\.            # ellipsis
        | [.,;"?:]  # these are separate tokens
        | [][()_`\|\n-]+  # these tokens are grouped; includes ] and [ and -
        ''')

        self.word_tokenizer = nltk.RegexpTokenizer(self.TokenPatternTB)

        if ndf:
            logging.info("Reading the normalization dictionary from {}...".format(ndf))
            self.read_normalization_dict(ndf)
            # print_time(" done: ")

        # print_time(" done: ")
