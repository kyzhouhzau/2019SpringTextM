#!/usr/bin/python
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
import os
import logging
from Token import Token
import Mention
# import nltk
# # choose nltk_data location for my laptop: update as needed for your machine
# nltk.data.path = ( ['nltk_data'] if os.path.exists('nltk_data') else  ['/vol/datailes/tools/nlp/nltk_data/2016'] )


#================
class Text(object):
    """Processing and representation of a text.

        string: the text contents as a raw string
        nlp_processor: language specifications for how to process the text
        sentences: list of sentences, as strings
        sent_spans: list of sentences, as spans consisting of (begin, end) offsets
        tokens: list of tokens, as strings
        token_spans: list of tokens, as spans consisting of (begin, end) offsets
    """

    def __init__(self, string, nlp_processor=None):
        self.string = string
        self.nlp_processor = nlp_processor
        logging.debug("Using language support {} to call {}".format(self.nlp_processor, self.nlp_processor.tokenize_word_punct))
        # self.tokens = (self.nlp_processor.word_tokenizer(self.string) if self.nlp_processor is not None else self.string.split(sep=" ")) # split on spaces if no tokenizer
        self.sentence_split()   # split text into sentences
        self.word_tokenize()    # split each sentence into tokens
        self.index_tokens() # index the tokens according to their offsets
        logging.info("Created {}".format(self))
        return

    def sentence_split(self):
        # self.sent_spans = (self.nlp_processor.sent_tokenizer.span_tokenize(self.string) if self.nlp_processor is not None else [ (0, len(self.string)) ]) # one sentence if no sentence splitter

        logging.debug("Splitting text into lines")
        # split the text into lines
        self.line_spans = []
        l = len(self.string)
        b = 0
        e = self.string.find("\n", b)
        while e >= 20:          # why 20?
            self.line_spans.append( (b, e) )
            b = e+1
            e = self.string.find("\n", b)
            # logging.info("sentence_split: line {}:{}".format(b, e))
        if b < l:
            self.line_spans.append( (b, len(self.string)) )

        splitter_spans = (self.nlp_processor.sent_tokenizer.span_tokenize if self.nlp_processor is not None else lambda s: [ (0, len(line)) ])
        logging.debug("Splitting text lines into sentences with {}".format(splitter_spans))
        self.sent_spans = []
        # split each line into sentences
        for line_b, line_e in self.line_spans:
            # logging.info("sentence_split: line {}:{}".format(line_b, line_e))
            line = self.string[line_b:line_e]
            logging.debug("Splitting line '{}' into sentences".format(line))
            # sent_spans = (self.nlp_processor.sent_tokenizer.span_tokenize(line) if self.nlp_processor is not None else [ (0, len(line)) ]) # one sentence if no sentence splitter
            sent_spans = splitter_spans(line)
            self.sent_spans.extend( [ (line_b+b, line_b+e) for b,e in sent_spans ] )

        if self.string == "":
            self.sentences = ()
        else:
            self.sentences = [ self.string[b:e] for b, e in self.sent_spans ]
            # self.sentences = []
            # for b, e in self.sent_spans:
            #     self.sentences.append( self.string[b:e] )
        return

    def word_tokenize(self):
        """Perform word tokenization within each sentence, and record offset of each token"""
        self.tokens = []
        if self.string == "":
            return
        else:
            # compute each token's offset and add token and absolute offset to text representation
            splitter_spans = self.nlp_processor.word_tokenizer.span_tokenize
            logging.debug("Splitting sentences into tokens with {}".format(splitter_spans))
            for i, sent in enumerate(self.sentences):
                if sent != "":  # no tokens in empty sentence
                    logging.debug("Splitting sentence '{}' of length {}".format(i, len(sent)))
                    sent_b, sent_e = self.sent_spans[i]
                    logging.debug("Splitting sentence '{}':{}-{} into tokens".format(sent, sent_b, sent_e))
                    # for b,e in self.nlp_processor.word_tokenizer.span_tokenize(sent):
                    for b,e in splitter_spans(sent):
                        self.tokens.append(Token(sent[b:e], (sent_b+b, sent_b+e)))
                        # self.tokens.append( sent[b:e] )
                        # self.token_spans.append( (sent_b+b, sent_b+e) )
        return

    def index_tokens(self):
        """Index each token's offsets:
        At each character position:
        * if there is a token, record (t, j) where
            t is the token
            j is the position of the current character in the token (starting with 0)
        * if there is no token (position between tokens), record the empty tuple ()
        This will serve to find which tokens belong to a mention."""
        self.token_offsets = [ () for i in range(self.string_len()+1) ] # one position per character + end
        for t in self.tokens:
            b, e = t.span
            for j in range(0, e-b):
                logging.debug("index_tokens: {}:{}:{}".format(b+j, t, j))
                self.token_offsets[b+j] = (t, j) # (token, position in token)
        return

    def register_mention_in_tokens(self, m):
        """Determine the list of tokens that belong to a mention, based upon their character offsets.
        [Use this later to apply B-I-O (or I-O-E, etc.) scheme.  This will serve in the CONLL representation of the mentions]"""
        # self.token_mentions = [ [] for i in range(self.string_len()+1) ] # one position per character + end
        logging.debug("register_mention_in_tokens: {}".format(m))
        tokens = []
        for b,e in m.spans:
            for i in range(b, e):
                token_offset = self.token_offsets[i]
                logging.debug("register_mention_in_tokens:  mention {}".format(token_offset))
                if len(token_offset) == 2:
                    t, j = token_offset
                    if j == 0 or len(tokens) == 0: # not yet seen this token: add it to the list
                        tokens.append(t)
        last = len(tokens) - 1
        for i, t in enumerate(tokens):
            t.register_mention(m, is_first=(i==0), is_last=(i==last))
        return tokens

    def __repr__(self):
        return "<Text of length {} with {} sentences and {} tokens>".format(len(self.string), len(self.sentences), len(self.tokens))

    def sprint(self, convert_eol=False):
        logging.info("Printing {}".format(self))
        if convert_eol:
            return self.string.replace("\n", " ")
        else:
            return self.string

    def print_conll(self, with_offset=False, with_labels=False, output=sys.stdout, filename="", scheme="OBBII", features=[], offset=0):
        """Prints to output the tokens of this Text in CONLL format, i.e., one token per line.

        output: an output stream to print to.
        with_offset: if True, adds a column with the filename and the offsets (b, e) of the token, in the form filename:b:e
        filename: the filename to use in with_offset (default "")
        with_labels: if True, adds a column with gold standard labels, using the provided scheme.
        scheme: if None, the fold standard labels are only the mention type.
          Otherwise, it must be a sequence of five strings:
          the prefixes to insert before the entity type in the gold standard label (separated by a '-'):
            0. for outside any entity, else
            1. for mono-token entity, else
            2. for first token, else
            3. for last token, else
            4. for inside token.
        features: list of feature objects
        
        Note: cannot handle overlapping mentions.
        In case this happens, i.e., a token belongs to multiple mentions,
        only prints the first mention for this token.
        """
        nb_sent = len(self.sent_spans)
        sent_id = 0
        sent_e = self.sent_spans[sent_id][1]
        for t in self.tokens: # loop on tokens
            b, e = t.span     # obtain token offsets
            if e > sent_e: # check whether we are in the next sentence
                sent_id += 1
                if sent_id >= nb_sent:
                    break
                sent_e = self.sent_spans[sent_id][1]
                print("", file=output)

            extras = []
            if with_offset:
                b, e = t.span
                extras.append("{}:{}:{}".format(filename, b, e-b))

            if len(features) > 0:
                for f in features:
                    extras.append(str(f.feature(t.sprint())))

            if with_labels:
                if scheme is None:
                    extras.append(mention.t)
                elif len(scheme) != 5:
                    raise ValueError ("The length of the label scheme is {} instead of 5".format(len(scheme)))
                else:
                    mentions = t.mentions
                    if len(mentions) == 0:
                        extras.append(scheme[0])
                    else:
                        (m, is_first, is_last) = mentions[0] # discard others if more than the first
                        if is_first and is_last:
                            prefix = scheme[1]
                        elif is_first:
                            prefix = scheme[2]
                        elif is_last:
                            prefix = scheme[3]
                        else:
                            prefix = scheme[4]
                        extras.append("-".join([prefix, m.t]))

            print("\t".join([t.sprint(convert_eol=True, replace_eol_with="\\n"), *extras]), file=output)
        return

    def string_len(self):
        return len(self.string)

    def __len__(self):
        return len(self.tokens)

    def __iter__(self):
        return (e for e in self.tokens)

    def __contains__(self, key):
        return tok in self.tokens

    def __geitem__(self, i):
        return self.tokens[i]

#================
if __name__ == '__main__':
    # to help test this program
    import logging
    logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    import NlpSupport
    example = """    6.1 Clinical Trials Experience  

  Because clinical trials are conducted under widely varying conditions, adverse reaction rates observed in the clinical trials of a drug cannot be directly compared to rates in the clinical trials of another drug and may not reflect the rates observed in practice.



 During its development for the adjunctive treatment of seizures associated with LGS, ONFI was administered to 333 healthy volunteers and 300 patients with a current or prior diagnosis of LGS, including 197 patients treated for 12 months or more. The conditions and duration of exposure varied greatly and included single- and multiple-dose clinical pharmacology studies in healthy volunteers and two double-blind studies in patients with LGS (Study 1 and 2)  [see Clinical Studies (  14  )]  . Only Study 1 included a placebo group, allowing comparison of adverse reaction rates on ONFI at several doses to placebo.
"""
    t = Text(example, nlp_processor=NlpSupport.NlpSupportEnglish())
    print(t)
    t.print_conll(with_offset=True, filename='example')
