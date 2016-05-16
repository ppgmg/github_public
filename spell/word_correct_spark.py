'''
word_correct_spark.py

################

You should have spark-1.5.0 or above installed, and be able to execute
spark-submit from your current directory.

to run:
spark-submit word_correct_spark.py -w "<word to correct>" 

You can also add a -d file.txt to specify a different dictionary file.
To use defaults, make sure the dictionary "big.txt" is in the current 
working directory.

Corrections are logged to "log.txt" in the local directory. Change the 
value of LOG from True to False to print to standard output.

################

v 3.0 last revised 26 Nov 2015

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

Future improvements may entail allowing for less verbose options, 
including the output of a single recommended correction. Note also that we
have generally kept to the form of the original program, and have not
introduced any major optimizations or structural changes in this PySpark port.


################

Example output:

################

Creating dictionary...
total words processed: 1105285
total unique words in corpus: 29157
total items in dictionary (corpus words and deletions): 2151998                 
  edit distance for deletions: 3
  length of longest word in corpus: 18
 
Word correction
---------------
finding corrections for there ...
looking up suggestions based on input word...
number of possible corrections: 604                                             
  edit distance for deletions: 3
[(u'there', (2972, 0)), (u'these', (1231, 1)), (u'where', (977, 1))...


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

def get_suggestions(s, masterdict, longest_word_length=float('inf'), silent=False):
    '''return list of suggested corrections for potentially incorrectly spelled word.
    
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
    # initialize suggestions RDD
    # suggestRDD entries: (word, (frequency of word in corpus, edit distance))
    #
    ##########
    
    ## since the dictionary will only be a lookup table once created, we can
    ## keep as Python dictionary rather than converting to RDD 
    ##### try broadcasting to workers for efficiency
    masterdict2 = sc.broadcast(masterdict)
    
    if not silent:
        print "looking up suggestions based on input word..."
    
    got_suggestions = False  # initialize flag
    init_sugg = []
    
    # check if input word is in dictionary, and is a word from the corpus (edit distance = 0)
    # if so, add input word itself and suggestions to suggestRDD
    
    if s in masterdict2.value:
        got_suggestions = True
        # dictionary values are in the form of ([suggestions], freq)
        if masterdict2.value[s][1]>0:  # frequency>0 -> real corpus word
            init_sugg = [(s, (masterdict2.value[s][1], 0))]

        # the suggested corrections for the item in dictionary (whether or not
        # the input string s itself is a valid word or merely a delete) can be 
        # valid corrections  -- essentially we serialize this portion since
        # the list of corrections tends to be very short
        
        add_sugg = [(sugg, (masterdict2.value[sugg][1], len(sugg)-len(s))) 
                        for sugg in masterdict2.value[s][0]]
        
        suggestRDD = sc.parallelize(init_sugg + add_sugg, n_partitions).cache()
        
    ##########
    #
    # process deletes on the input string 
    #
    ##########
     
    assert max_edit_distance>0
    
    list_deletes_of_s = get_n_deletes_list(s, max_edit_distance)  # this list is short
    
    add_sugg_2 = [(sugg, (masterdict2.value[sugg][1], len(s)-len(sugg))) 
                      for sugg in list_deletes_of_s if ((sugg in masterdict2.value) and
                                                        (masterdict2.value[sugg][1]>0))]
    
    add_sugg_2_RDD = sc.parallelize(add_sugg_2, n_partitions)
    
    if got_suggestions:
        suggestRDD = suggestRDD.union(add_sugg_2_RDD).cache()
    else:
        got_suggestions = True
        suggestRDD = add_sugg_2_RDD.cache()
        
    # check each item of suggestion list of all new-found suggestions 
    # the suggested corrections for the item in dictionary (whether or not
    # the delete itself is a valid word or merely a delete) can be valid corrections   
    # expand lists of list
    
    sugg_lists = [masterdict2.value[sugg][0] for sugg in list_deletes_of_s 
                      if sugg in masterdict2.value]
    sugg_lists_RDD = sc.parallelize(sugg_lists)
    list_sl = sugg_lists_RDD.flatMap(lambda x: x).map(lambda w: (w, 0))
    combine_del = list_sl.reduceByKey(lambda a, b: a + b, numPartitions = n_partitions).cache()

    # need to recalculate actual Deverau Levenshtein distance to be within max_edit_distance for all deletes
    calc_dist = combine_del.map(lambda (w, _): (w, dameraulevenshtein(s, w)),
                                       preservesPartitioning=True)
    filter_by_dist = calc_dist.filter(lambda (w, dist): dist<=max_edit_distance)
    
    # get frequencies from main dictionary and add to suggestions list
    get_freq = filter_by_dist.filter(lambda (w, dist): w in masterdict2.value)
    del_parent_sugg = get_freq.map(lambda (w, dist): (w, (masterdict2.value[w][1], dist)),
                                     preservesPartitioning=True)
    
    if got_suggestions:
        if len(sugg_lists)>0:
            suggestRDD = suggestRDD.union(del_parent_sugg).distinct().cache()
        else:
            # no additional suggestions, leave suggest RDD intact
            pass
        
        # convert unicode to string (currently input not in unicode)
        suggestRDD = suggestRDD.map(lambda (w, _): (str(w), _)).cache()
    else:
        suggestRDD = sc.EmptyRDD() 
                   
    if not silent:
        print "number of possible corrections: %i" % suggestRDD.count()
        print "  edit distance for deletions: %i" % max_edit_distance

    ##########
    #
    # optionally, sort RDD for output
    #
    ##########
    
    # suggest_RDD is in the form: [(word, (freq, editdist)), (word, (freq, editdist)), ...]
    # there does not seem to be a straightforward way to sort by both primary and secondary keys in Spark
    # this is a documented issue: one option is to simply work with a list since there are likely not
    # going to be an extremely large number of recommended suggestions
    
    output = suggestRDD.collect()
    
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

def best_word(s, d, l, silent=False):
    a = get_suggestions(s, d, l, silent)
    if len(a)==0:
        return (None, (None, None))
    else: 
        return a[0]

def main(argv):
    '''
    Parses command line parameters (if any).

    Command line parameters are expected to take the form:
    -d : dictionary file
    -w : word to correct

    Default values are applied where files are not provided.
    https://docs.python.org/2/library/getopt.html
    '''

    # default values - use if not overridden
    dictionary_file = 'big.txt'
    word_in = ''

    # read in command line parameters
    try:
        opts, args = getopt.getopt(argv,'d:w:',['dfile=','word='])
    except getopt.GetoptError:
        print 'word_correct_spark.py -d <dfile> -w <word>'

    # parse command line parameters    
    for opt, arg in opts:
        if opt in ('-d', '--dictionary'):
            dictionary_file = arg
        elif opt in ('-w', '--word'):
            word_in = arg

    # return command line parameters (or default values if not provided)
    return dictionary_file, word_in

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
    dictionary_file, word_in = main(sys.argv[1:])

    if not os.path.isfile(dictionary_file):
        dictionary_file = "testdata/big.txt"
        if not os.path.isfile(dictionary_file):
            print 'Invalid dictionary file. Could not run.'
            sys.exit()

    if word_in == '':
        print "No word was provided for checking. Please use -w 'word' tag."
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
    print "Word correction"
    print "---------------"

    print "finding corrections for: %s ..." % word_in
    start_time = time.time()
    out = get_suggestions(word_in, d, lwl)
    if LOG:
        if len(out)>0:
            print "top match: %s" % str(out[0])
        f = open('log.txt', 'w')
        f.write(str(out))
        f.close()
        print "Check <log.txt> for details of other suggested corrections."
    else:
        print out
    run_time = time.time() - start_time
    print '-----'
    print '%.2f seconds to run' % run_time
    print '-----'
    print " "