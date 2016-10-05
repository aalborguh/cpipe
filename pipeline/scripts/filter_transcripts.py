#!/usr/bin/env python
'''
###########################################################################
#
# This file is part of Cpipe.
#
# Cpipe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, under version 3 of the License, subject
# to additional terms compatible with the GNU General Public License version 3,
# specified in the LICENSE file that is part of the Cpipe distribution.
#
# Cpipe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cpipe.    If not, see <http:#www.gnu.org/licenses/>.
#
###########################################################################
# Purpose:
#   filter tab separated output based on the transcript:
#   remove XMs that have an NM at the same location
# Usage:
#   filter_transcripts.py < variants.tsv 1>filtered.tsv
####################################################################################
'''

import argparse
import collections
import datetime
import sys

TRANSCRIPT_COLUMN = 'Feature'
IDENTIFYING_COLUMNS = ['CHROM', 'POS', 'REF', 'ALT']

def filter_tsv(instream, outstream, log):
    '''
        read instream and filter out XM transcripts that are in a location that already has an NM transcript
    '''
    # get header
    first = True
    include = collections.defaultdict(list)
    has_nm = set()
    log.write('reading...\n')
    count = 0
    counts = {'nm_orig': 0, 'xm_orig': 0, 'other_orig': 0, 'nm_new': 0, 'xm_new': 0}
    for count, line in enumerate(instream):
        if first: # get header info
            first = False
            header_line = line
            header = line.strip('\n').split('\t')
            if TRANSCRIPT_COLUMN not in header:
                log.write('ERROR: {} not found in header\n'.format(TRANSCRIPT_COLUMN))
                return
            transcript_idx = header.index(TRANSCRIPT_COLUMN)
            identifiers = []
            for identifier in IDENTIFYING_COLUMNS:
                if identifier not in header:
                    log.write('ERROR: {} not found in header\n'.format(identifier))
                    return
                identifiers.append(header.index(identifier))
        else:
            # build identifier
            fields = line.strip('\n').split('\t')
            identifier = '\t'.join([fields[x] for x in identifiers])
            transcript = fields[transcript_idx]
            if transcript.startswith('NM_'):
                if identifier not in has_nm: # first seen NM -> remove any existing XMs
                    new_list = [ line ]
                    for old_item in include[identifier]:
                        old_item_transcript = old_item.strip('\n').split('\t')[transcript_idx]
                        if not old_item_transcript.startswith('XM_'):
                            new_list.append(old_item)
                    include[identifier] = new_list
                else: # already seen an NM, add another NM
                    include[identifier].append(line)
                has_nm.add(identifier) 
                counts['nm_orig'] += 1
            elif transcript.startswith('XM_'):
                if identifier in has_nm:
                    pass # don't add XM -> already has an NM
                else:
                    include[identifier].append(line)
                counts['xm_orig'] += 1
            else: # include anything else
                include[identifier].append(line)
                counts['other_orig'] += 1
    log.write('read {} lines\n'.format(count))

    # write out filtered            
    count = 0
    outstream.write(header_line)
    for identifier in include:
        for line in include[identifier]:
            transcript = line.strip('\n').split('\t')[transcript_idx]
            if transcript.startswith('NM_'):
                counts['nm_new'] += 1
            elif transcript.startswith('XM_'):
                counts['xm_new'] += 1
            outstream.write(line)
            count += 1
    log.write('done writing {} lines. stats: {}\n'.format(count, counts))

def main():
    '''
        run from command line
    '''
    parser = argparse.ArgumentParser(description='Filter TSV')
    args = parser.parse_args()
    filter_tsv(sys.stdin, sys.stdout, sys.stderr)

if __name__ == '__main__':
    main()
