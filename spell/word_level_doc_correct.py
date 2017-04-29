'''
word_level_doc_correct.py

################

You should have spark-1.5.0 or above installed, and be able to execute
spark-submit from your current directory.

to run:
spark-submit word_level_doc_correct.py -c "<.txt file to check>" 

You can also add a -d file.txt to specify a different dictionary file.
To use defaults, make sure the dictionary "big.txt", and the test document
"test.txt" are in the current working directory.

Corrections are logged to "log.txt" in the local directory. Change the 
value of LOG from True to False to print to standard output.

################

v 4.1 last revised 29 Apr 2017
Please note this code is no longer being maintained.

License:
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License, 
version 3.0 (LGPL-3.0) as published by the Free Software Foundation.
http://www.opensource.org/licenses/LGPL-3.0

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.

Please acknowledge Wolf Garbe, as the original creator of SymSpell,
(see note below) in any use.

################

This program is a Spark (PySpark) version of a spellchecker based on SymSpell, 
a Symmetric Delete spelling correction algorithm developed by Wolf Garbe 
and originally written in C#.

From the original SymSpell documentation:

"The Symmetric Delete spelling correction algorithm reduces the complexity 
 of edit candidate generation and dictionary lookup for a given Damerau-
 Levenshtein distance. It is six orders of magnitude faster and language 
 independent. Opposite to other algorithms only deletes are required, 
 no transposes + replaces + inserts. Transposes + replaces + inserts of the 
 input term are transformed into deletes of the dictionary term.
 Replaces and inserts are expensive and language dependent: 
 e.g. Chinese has 70,000 Unicode Han characters!"

For further information on SymSpell, please consult the original documentation:
  URL: blog.faroo.com/2012/06/07/improved-edit-distance-based-spelling-correction/
  Description: blog.faroo.com/2012/06/07/improved-edit-distance-based-spelling-correction/

The current version of this program will output all possible suggestions for
corrections up to an edit distance (configurable) of max_edit_distance = 3. 

IMPORTANT NOTE:  The current version will generate internally all possible
correction for each word in the test document before choosing the best one.
This allows us to compare the performance of earlier versions of the code.
This means that this code will run slowly for any moderately-sized test file.

################

Example output:

################

Please wait...
Creating dictionary...
total words processed: 1105285                                                  
total unique words in corpus: 29157
total items in dictionary (corpus words and deletions): 2151998                 
  edit distance for deletions: 3
  length of longest word in corpus: 18
 
Document correction... Please wait...
-------------------------------------
finding corrections for: test.txt ...
Finding misspelled words in your document...
    Unknown words (line number, word in text):
[]                                                                              
    Words with suggested corrections (line number, word in text, top match):
[(4, 'za --> a'), (6, 'tee --> the')]                                           
-----
total words checked: 27
total unknown words: 0
total potential errors found: 2


'''

from pyspark import SparkContext
sc = SparkContext()

import re

n_partitions = 6  # number of partitions to be used
max_edit_distance = 3
LOG = True  # log correction output

# helper functions
def get_n_deletes_list(w, n):
    '''given a word, derive list of strings with up to n characters deleted'''
    # since this list is generally of the same magnitude as the number of 
    # characters in a word, it may not make sense to parallelize this
    # so we use python to create the list
    deletes = []
    queue = [w]
    for d in range(n):
        temp_queue = []
        for word in queue:
            if len(word)>1:
                for c in range(len(word)):  # character index
                    word_minus_c = word[:c] + word[c+1:]
                    if word_minus_c not in deletes:
                        deletes.append(word_minus_c)
                    if word_minus_c not in temp_queue:
                        temp_queue.append(word_minus_c)
        queue = temp_queue
        
    return deletes
    
def copartitioned(RDD1, RDD2):
    '''check if two RDDs are copartitioned'''
    return RDD1.partitioner == RDD2.partitioner

def combine_joined_lists(tup):
    '''takes as input a tuple in the form (a, b) where each of a, b may be None (but not both) or a list
       and returns a concatenated list of unique elements'''
    concat_list = []
    if tup[1] is None:
        concat_list = tup[0]
    elif tup[0] is None:
        concat_list = tup[1]
    else:
        concat_list = tup[0] + tup[1]
        
    return list(set(concat_list))

def parallel_create_dictionary(fname):
    '''Create dictionary using Spark RDDs.'''
    # we generate and count all words for the corpus,
    # then add deletes to the dictionary
    # this is a slightly different approach from the SymSpell algorithm
    # that may be more appropriate for Spark processing
    
    print "Creating dictionary..." 
    
    ############
    #
    # process corpus
    #
    ############
    
    # http://stackoverflow.com/questions/22520932/python-remove-all-non-alphabet-chars-from-string
    regex = re.compile('[^a-z ]')

    # convert file into one long sequence of words
    make_all_lower = sc.textFile(fname).map(lambda line: line.lower())
    replace_nonalphs = make_all_lower.map(lambda line: regex.sub(' ', line))
    all_words = replace_nonalphs.flatMap(lambda line: line.split())

    # create core corpus dictionary (i.e. only words appearing in file, no "deletes") and cache it
    # output RDD of unique_words_with_count: [(word1, count1), (word2, count2), (word3, count3)...]
    count_once = all_words.map(lambda word: (word, 1))
    unique_words_with_count = count_once.reduceByKey(lambda a, b: a + b, numPartitions = n_partitions).cache()
    
    # output stats on core corpus
    print "total words processed: %i" % unique_words_with_count.map(lambda (k, v): v).reduce(lambda a, b: a + b)
    print "total unique words in corpus: %i" % unique_words_with_count.count()
    
    ############
    #
    # generate deletes list
    #
    ############
    
    # generate list of n-deletes from words in a corpus of the form: [(word1, count1), (word2, count2), ...]
     
    assert max_edit_distance>0  
    
    generate_deletes = unique_words_with_count.map(lambda (parent, count): 
                                                   (parent, get_n_deletes_list(parent, max_edit_distance)))
    expand_deletes = generate_deletes.flatMapValues(lambda x: x)
    swap = expand_deletes.map(lambda (orig, delete): (delete, ([orig], 0)))
   
    ############
    #
    # combine delete elements with main dictionary
    #
    ############
    
    corpus = unique_words_with_count.mapValues(lambda count: ([], count))
    combine = swap.union(corpus)  # combine deletes with main dictionary, eliminate duplicates
    
    ## since the dictionary will only be a lookup table once created, we can
    ## pass on as a Python dictionary rather than RDD by reducing locally and
    ## avoiding an extra shuffle from reduceByKey
    new_dict = combine.reduceByKeyLocally(lambda a, b: (a[0]+b[0], a[1]+b[1]))
    
    print "total items in dictionary (corpus words and deletions): %i" % len(new_dict)
    print "  edit distance for deletions: %i" % max_edit_distance
    longest_word_length = unique_words_with_count.map(lambda (k, v): len(k)).reduce(max)
    print "  length of longest word in corpus: %i" % longest_word_length

    return new_dict, longest_word_length    

def dameraulevenshtein(seq1, seq2):
    """Calculate the Damerau-Levenshtein distance (an integer) between sequences.

    This code has not been modified from the original.
    Source: http://mwh.geek.nz/2009/04/26/python-damerau-levenshtein-distance/
    
    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects will work.

    Transpositions are exchanges of *consecutive* characters; all other
    operations are self-explanatory.

    This implementation is O(N*M) time and O(M) space, for N and M the
    lengths of the two sequences.

    >>> dameraulevenshtein('ba', 'abc')
    2
    >>> dameraulevenshtein('fee', 'deed')
    2

    It works with arbitrary sequences too:
    >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
    2
    """
    # codesnippet:D0DE4716-B6E6-4161-9219-2903BF8F547F
    # Conceptually, this is based on a len(seq1) + 1 * len(seq2) + 1 matrix.
    # However, only the current and two previous rows are needed at once,
    # so we only store those.
    oneago = None
    thisrow = range(1, len(seq2) + 1) + [0]
    for x in xrange(len(seq1)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in xrange(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                and seq1[x-1] == seq2[y] and seq1[x] != seq2[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
    return thisrow[len(seq2) - 1]

def no_RDD_get_suggestions(s, masterdict, longest_word_length=float('inf'), silent=False):
    '''return list of suggested corrections for potentially incorrectly spelled word.
    
    Note: serialized version for Spark document correction.
    
    s: input string
    masterdict: the main dictionary (python dict), which includes deletes
             entries, is in the form of: {word: ([suggested corrections], 
                                                 frequency of word in corpus), ...}
    longest_word_length: optional identifier of longest real word in masterdict
    silent: verbose output (when False)
    '''

    if (len(s) - longest_word_length) > max_edit_distance:
        if not silent:
            print "no items in dictionary within maximum edit distance"
        return []

    ##########
    #
    # initialize suggestions list
    # suggestList entries: (word, (frequency of word in corpus, edit distance))
    #
    ##########
    
    if not silent:
        print "looking up suggestions based on input word..."
    
    suggestList = []
    
    # check if input word is in dictionary, and is a word from the corpus (edit distance = 0)
    # if so, add input word itself and suggestions to suggestRDD
    
    if s in masterdict:
        init_sugg = []
        # dictionary values are in the form of ([suggestions], freq)
        if masterdict[s][1]>0:  # frequency>0 -> real corpus word
            init_sugg = [(str(s), (masterdict[s][1], 0))]

        # the suggested corrections for the item in dictionary (whether or not
        # the input string s itself is a valid word or merely a delete) can be 
        # valid corrections  -- essentially we serialize this portion since
        # the list of corrections tends to be very short
        
        add_sugg = [(str(sugg), (masterdict[sugg][1], len(sugg)-len(s))) 
                        for sugg in masterdict[s][0]]
        
        suggestList = init_sugg + add_sugg
        
    ##########
    #
    # process deletes on the input string 
    #
    ##########
     
    assert max_edit_distance>0
    
    list_deletes_of_s = get_n_deletes_list(s, max_edit_distance)  # this list is short
    
    # check suggestions is in dictionary and is a real word
    add_sugg_2 = [(str(sugg), (masterdict[sugg][1], len(s)-len(sugg))) 
                      for sugg in list_deletes_of_s if ((sugg in masterdict) and
                                                        (masterdict[sugg][1]>0))]
    
    suggestList += add_sugg_2
        
    # check each item of suggestion list of all new-found suggestions 
    # the suggested corrections for any item in dictionary (whether or not
    # the delete itself is a valid word or merely a delete) can be valid corrections   
    # expand lists of list
    
    sugg_lists = [masterdict[sugg][0] for sugg in list_deletes_of_s if sugg in masterdict]
    list_sl = [(val, 0) for sublist in sugg_lists for val in sublist]
    combine_del = list(set((list_sl))) 

    # need to recalculate actual Deverau Levenshtein distance to be within 
    # max_edit_distance for all deletes; also check that suggestion is a real word
    filter_by_dist = []
    for item in combine_del:
        calc_dist = dameraulevenshtein(s, item[0])
        if (calc_dist<=max_edit_distance) and (item[0] in masterdict):
            filter_by_dist += [(item[0], calc_dist)]
        
    # get frequencies from main dictionary and add new suggestions to suggestions list
    suggestList += [(str(item[0]), (masterdict[item[0]][1], item[1]))
                            for item in filter_by_dist]
    
    output = list(set(suggestList))
    
    if not silent:
        print "number of possible corrections: %i" % len(output)
        print "  edit distance for deletions: %i" % max_edit_distance

    ##########
    #
    # optionally, sort RDD for output
    #
    ##########
    
    # output option 1
    # sort results by ascending order of edit distance and descending order of frequency
    #     and return list of suggested corrections only:
    # return sorted(output, key = lambda x: (suggest_dict[x][1], -suggest_dict[x][0]))

    # output option 2
    # return list of suggestions with (correction, (frequency in corpus, edit distance)):
    # return sorted(output, key = lambda (term, (freq, dist)): (dist, -freq))

    if len(output)>0:
        return sorted(output, key = lambda (term, (freq, dist)): (dist, -freq))
    else:
        return []
    
def correct_document(fname, d, lwl=float('inf'), printlist=True):
    '''Correct an entire document using word-level correction.
    
    Note: Uses a serialized version of an individual word checker. 
    
    fname: filename
    d: the main dictionary (python dict), which includes deletes
             entries, is in the form of: {word: ([suggested corrections], 
                                                 frequency of word in corpus), ...}
    lwl: optional identifier of longest real word in masterdict
    printlist: identify unknown words and words with error (default is True)
    '''
    
    # broadcast lookup dictionary to workers
    bd = sc.broadcast(d)
    
    print "Finding misspelled words in your document..." 
    
    # http://stackoverflow.com/questions/22520932/python-remove-all-non-alphabet-chars-from-string
    regex = re.compile('[^a-z ]')

    # convert file into one long sequence of words with the line index for reference
    make_all_lower = sc.textFile(fname).map(lambda line: line.lower()).zipWithIndex()
    replace_nonalphs = make_all_lower.map(lambda (line, index): (regex.sub(' ', line), index))
    flattened = replace_nonalphs.map(lambda (line, index): 
                                 [(i, index) for i in line.split()]).flatMap(list)
    
    # create RDD with (each word in document, corresponding line index) 
    # key value pairs and cache it
    all_words = flattened.partitionBy(n_partitions).cache()
    
    # check all words in parallel --  stores whole list of suggestions for each word
    get_corrections = all_words.map(lambda (w, index): 
                                    (w, (no_RDD_get_suggestions(w, bd.value, lwl, True), index)),
                                     preservesPartitioning=True).cache()
    
    # UNKNOWN words are words where the suggestion list is empty
    unknown_words = get_corrections.filter(lambda (w, (sl, index)): len(sl)==0)
    if printlist:
        print "    Unknown words (line number, word in text):"
        print unknown_words.map(lambda (w, (sl, index)): (index, str(w))).sortByKey().collect()
    
    # ERROR words are words where the word does not match the first tuple's word (top match)
    error_words = get_corrections.filter(lambda (w, (sl, index)): len(sl)>0 and w!=sl[0][0]) 
    if printlist:
        print "    Words with suggested corrections (line number, word in text, top match):"
        print error_words.map(lambda (w, (sl, index)): 
                                 (index, str(w) + " --> " +
                                         str(sl[0][0]))).sortByKey().collect()
    elif LOG:
        f = open('log.txt', 'w')
        f.write("    Unknown words (line number, word in text): \n")
        f.write(str(unknown_words.map(lambda (w, (sl, index)): (index, str(w))).sortByKey().collect()))
        f.write("\n    Words with suggested corrections (line number, word in text, top match): \n")
        f.write(str(error_words.map(lambda (w, (sl, index)): 
                                 (index, str(w) + " --> " +
                                         str(sl[0][0]))).sortByKey().collect()))
        f.close()
        print "Check <log.txt> for details of suggested corrections."
    
    gc = sc.accumulator(0)
    get_corrections.foreach(lambda x: gc.add(1))
    uc = sc.accumulator(0)
    unknown_words.foreach(lambda x: uc.add(1))
    ew = sc.accumulator(0)
    error_words.foreach(lambda x: ew.add(1))
    
    print "-----"
    print "total words checked: %i" % gc.value
    print "total unknown words: %i" % uc.value
    print "total potential errors found: %i" % ew.value

    return

def main(argv):
    '''
    Parses command line parameters (if any).

    Command line parameters are expected to take the form:
    -d : dictionary file
    -c : .txt document file to check

    Default values are applied where files are not provided.
    https://docs.python.org/2/library/getopt.html
    '''

    # default values - use if not overridden
    dictionary_file = 'big.txt'
    check_file = 'test.txt'

    # read in command line parameters
    try:
        opts, args = getopt.getopt(argv,'d:c:',['dfile=','cfile='])
    except getopt.GetoptError:
        print 'spark_4.py -d <dfile> -c <cfile>'
        print 'Default values will be applied.'

    # parse command line parameters    
    for opt, arg in opts:
        if opt in ('-d', '--dictionary'):
            dictionary_file = arg
        elif opt in ('-c', '--cfile'):
            check_file = arg

    # return command line parameters (or default values if not provided)
    return dictionary_file, check_file

## main

import time
import sys
import getopt
import os

if __name__ == "__main__":
    

    ############
    #
    # get inputs and check that they are valid
    #
    ############

    # dictionary_file = used for pre-processing steps
    # check_file = text to be spell-checked
    dictionary_file, check_file = main(sys.argv[1:])

    dict_valid = os.path.isfile(dictionary_file)
    check_valid = os.path.isfile(check_file)

    if not dict_valid and not check_valid:
        dictionary_file = "testdata/big.txt"
        check_file = "testdata/test.txt"
        dict_valid = os.path.isfile(dictionary_file)
        check_valid = os.path.isfile(check_file)
        if not dict_valid and not check_valid:
            print 'Invalid dictionary and document-to-check files. Could not run.'
            sys.exit()
    elif not dict_valid:
        dictionary_file = "testdata/big.txt"
        dict_valid = os.path.isfile(dictionary_file)
        if not dict_valid:
            print 'Invalid dictionary file. Could not run.'
            sys.exit()
    elif not check_valid:
        check_file = "testdata/test.txt"
        check_valid = os.path.isfile(check_file)
        if not check_valid:
            print 'Invalid document-to-check file. Could not run.'
            sys.exit()

    ############
    #
    # run normally from here
    #
    ############

    print "Please wait..."
    time.sleep(2)
    start_time = time.time()
    d, lwl = parallel_create_dictionary(dictionary_file)
    run_time = time.time() - start_time
    print '-----'
    print '%.2f seconds to run' % run_time
    print '-----'

    print " "
    print "Document correction... Please wait..."
    print "-------------------------------------"

    print "finding corrections for: %s ..." % check_file
    start_time = time.time()
    correct_document(check_file, d, lwl, False)
    run_time = time.time() - start_time
    print '-----'
    print '%.2f seconds to run' % run_time
    print '-----'
    print " "
