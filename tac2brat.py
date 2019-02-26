#!/usr/bin/python
# Python 2-3 compatibility: see http://python-future.org/quickstart.html
#python tac2brat.py -d '/home/zhoukaiyin/Desktop/CRF_PRO/src/train_xml'  -o '/home/zhoukaiyin/Desktop/CRF_PRO/work/corpus/test' -F TokenDict:diso:dis-DISO-2.dic -t conll -s OBBEI
from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *

import sys
import os
import argparse
import logging
import re
import pdb
from lxml import etree
#  import nltk
# # choose nltk_data location for my laptop: update as needed for your machine
# nltk.data.path = ( ['nltk_data'] if os.path.exists('nltk_data') else  ['/vol/datailes/tools/nlp/nltk_data/2016'] )
from Mention import Mention, Relation
from Text import Text
from NlpSupport import NlpSupportEnglish
import Features


# Program version
version = '0.3'

#================
class Section(object):

    def __init__(self, id, name, string, mentions=[], nlp_processor=None, file=""):
        self.id = id
        self.name = name
        self.string = string
        self.nlp_processor = (nlp_processor if nlp_processor is not None else NlpSupportEnglish())
        self.file = file
        self.text = Text(self.string, nlp_processor=self.nlp_processor)
        self.mentions = []
        for m in mentions: # add mentions provided at init time
            self.add_mention(m)
        # self.text.add_mentions(self.mentions)
        logging.info("Created Section '{}' with name '{}'".format(self.id, self.name))

    def add_mention(self, m):
        logging.debug("add_mention: {}: {}".format(self, m))
        self.mentions.append(m)
        self.text.register_mention_in_tokens(m)
        return

    def print_mentions(self, offset=0, output=sys.stdout):
        for m in self.mentions:
            print(m.sprint(offset=offset), file=output)
        return

    def print_tokens_and_mentions(self, offset=0, output=sys.stdout, scheme="OBBII", features=[]):
        # for t in self.text.tokens:
        #     print(t, file=output)
        self.text.print_conll(with_offset=True, output=output, filename=":".join((self.file, self.id)), with_labels=True, offset=offset, scheme=scheme, features=features)
        return

    def sprint(self, convert_eol=False):
        return self.text.sprint(convert_eol=convert_eol)

    def __len__(self):
        return self.text.string_len()

    def __repr__(self):
        return "<Section '{}' of size {}>".format(self.id, len(self))

#================
class Converter(object):

    def __init__(self):
        pass

    def output_file_names(self, file, format='brat'):
        f = os.path.basename(file)
        f = re.sub("\.xml$", "", f)
        if format == 'brat':
            return os.path.join(self.output_dir, f + ".txt"), os.path.join(self.output_dir, f + ".ann")
        elif format == 'conll':
            return os.path.join(self.output_dir, f + ".tab")

    def convert_file_to_brat(self, file):
        output_t_file, output_a_file = self.output_file_names(file)
        logging.info("Reading from {} into {} + {}".format(file, output_t_file, output_a_file))
        with open(output_t_file, "w", encoding="utf-8") as tf:
            with open(output_a_file, "w", encoding="utf-8") as ta:
                self.load_file(file)
                self.print_brat_files(output_t=tf, output_a=ta)
                return

    def convert_file_to_conll(self, file, features=[]):
        output_t_file = self.output_file_names(file, format='conll')
        logging.info("Reading from {} into {}".format(file, output_t_file))
        with open(output_t_file, "w", encoding="utf-8") as tf:
            self.load_file(file)
            self.print_conll_file(output_t=tf, features=features)
            return

    def load_file(self, file):
        """Parse contents of file and create list of sections, mentions, and relations.

        Obtains and adds as slots of self:
        sections: list of Section objects (each contains a Text object and a list of Mention objects)
        mentions: list of Mention objects
        relations: list of Relation objects
        """
        tree = etree.parse(file)

        # parse sections and their texts
        self.sections = [ Section(s.get("id"), s.get("name"), s.text, file=os.path.basename(file)) for s in tree.xpath("/Label/Text/Section") ]
        sec_dict = { s.id: s for s in self.sections }

        self.mentions = []
        # parse mentions and add to their sections
        for x in tree.xpath("/Label/Mentions/Mention"):
            sec_id = x.get("section")
            if sec_id not in sec_dict:
                raise ValueError ( "Unknown section id: '{}', skipping mention".format(sec_id) )
            else:
                section = sec_dict[sec_id]

                m =  Mention.from_lxml(x)
                self.mentions.append(m)
                section.add_mention(m)
                logging.debug("% New mention {}:'{}' added to Section '{}'".format(sec_id, m.id, section.name))

        # parse relations
        self.relations = []
        for x in tree.xpath("/Label/Relations/Relation"):
            r =  Relation.from_lxml(x)
            self.relations.append(r)
            logging.debug("% New relation {}".format(r.id))

        return

    def print_brat_files(self, output_t=sys.stdout, output_a=sys.stdout):

        # print sections and their mentions
        o = 0
        for s in self.sections:
            logging.info("================ Section {} ================".format(s.id))
            # output_text.write(s.string)
            print(s.sprint(convert_eol=False), file=output_t, flush=True, end="") # no newline to avoid shift in offsets
            logging.info("==== Mentions for section {} ====".format(s.id))
            s.print_mentions(offset=o, output=output_a)
            o += len(s) # to obtain one consistent file, increment global offset

        # print relations
        for r in self.relations:
            print(r.sprint(), file=output_a)

        return

    def print_conll_file(self, output_t=sys.stdout, features=[]):

        # print sections (as tokens) and their mentions (as gold labels)
        o = 0
        for s in self.sections:
            logging.info("================ Section {} and its mentions ================".format(s.id))
            s.print_tokens_and_mentions(offset=o, output=output_t, scheme=self.scheme, features=features)
            o += len(s) # to obtain one consistent file, increment global offset

        return

#================================================================
    def parse_execute_command_line(self):
        parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=__doc__)

        groupI = parser.add_argument_group('Input')
        groupIE = groupI.add_mutually_exclusive_group(required=True)
        groupIE.add_argument('-f', '--file',
                            help="input file: an XML file")
        groupIE.add_argument("-d", "--directory",
                            help="input directory: all *.xml files in this directory will be processed")

        groupO = parser.add_argument_group('Output')
        groupO.add_argument("-o", "--output_directory", default=".",
                            help="output directory (default = current directory)")

        groupP = parser.add_argument_group('Processing')
        groupP.add_argument("-t", "--target-format", choices=["brat", "conll"], default="brat",
                            help="specify target format: brat (default: for display, creates .txt and .ann) or conll (for CRF, creates .tab)")
        groupP.add_argument("-s", "--scheme", default="OBBII", # = BIO
                            help="""specify scheme for labels: default = 'OBBII' which specifies the classical B-I-O scheme.
                            Use 'OBBEI' for B-I-E-O scheme.
                            Use 'OEIEI' for I-E-O scheme.
                            Use 'OIIII' for I-O scheme.
                            Must be a string of length 5, where each character position applies to the following case:
        0. for outside any entity, else
        1. for mono-token entity, else
        2. for first token, else
        3. for last token, else
        4. for inside token""")
        groupP.add_argument("-F", "--features", default="",
                            help="""for CONLL format only: specify features to add.
        Must be a comma-separated list of feature specifications.  Each specification must contain:
            1. a feature name. 2. optionally, a colon-separated list of arguments.
            Example: TokenDict:msh:msh-diso-1.dic
            The feature name must be a class name (see Features.py), the arguments are passed to the class creator.""")

        groupS = parser.add_argument_group('Special')
        groupS.add_argument("-q", "--quiet", action="store_true",
                            help="suppress reporting progress info")
        groupS.add_argument("--debug", action="store_true",
                            help="print debug info")
        groupS.add_argument("-v", "--version", action="version",
                            version='%(prog)s ' + version,
                            help="print program version")

        args = parser.parse_args()

        # process arguments and parameters
        FORMAT = '%(levelname)s: %(message)s'
        logging.basicConfig(format=FORMAT)

        logger = logging.getLogger()
        if not args.quiet:
            logger.setLevel(logging.INFO)
        if args.debug:
            logger.setLevel(logging.DEBUG)

        # actual processing
        self.scheme = args.scheme
        if len(self.scheme) != 5:
            raise ValueError ("The length of the label scheme is {} instead of 5".format(len(self.scheme)))

        f_objs = ( [] if args.features == "" else [ Features.FeatureParser(spec).f for spec in args.features.split(sep=",") ] )

	
        logging.info("{} features: '{}'.".format(len(f_objs), f_objs))

        self.output_dir = args.output_directory
        if not os.path.exists(self.output_dir):
            logging.info("Creating output directory '{}'.".format(self.output_dir))
            os.mkdir(self.output_dir)
        if not os.path.isdir(self.output_dir):
            raise NameError ("Output directory '{}' is a file instead of a directory".format(self.output_dir))
        if args.file:
            if args.target_format == 'brat':
                self.convert_file_to_brat(args.file)
            elif args.target_format == 'conll':
            	self.convert_file_to_conll(args.file, features=f_objs)

            logging.info("Processed {} XML file(s)".format(1))
        else:
            input_dir = args.directory
            logging.info("Reading from {}/*.xml into {}".format(input_dir, self.output_dir))
            n = 0
            for file in sorted(os.listdir(input_dir)):
                if file.endswith(".xml"):
                    file = os.path.join(input_dir, file) # do not forget to add the directory name to the file name!
                    if args.target_format == 'brat':
                        self.convert_file_to_brat(file)
                    elif args.target_format == 'conll':
                        self.convert_file_to_conll(file, features=f_objs)
                    n += 1
            logging.info("Processed {} XML file(s)".format(n))
        return

if __name__ == '__main__':
    # to help test this program
    c = Converter()
    c.parse_execute_command_line()
