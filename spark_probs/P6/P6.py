# P6.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 6
#
####################

'''
This program takes a word file and generates an RDD, with elements comprising:
1. a tuple of two words that appear in sequence
2. a list of tuples, each tuple containing
  i. a third word that appears in sequence after the pair of words in (1)
  ii. the number of times that third word appears in that sequence in the file

The program will also generate phrases of a pre-determined length, by randomly
selecting an initial two-word pair, and then selecting successive words biased
by its count when following that two-word pair in the file.

Notes: 

Text file (Shakespeare.txt) must be in the current directory.

I have deleted lines from the beginning and the end of the original input file
that included licensing terms, bibliographic info, and other such text.
No text was deleted from "1609" to the final "THE END".

Reference re: Spark actions that maintain order of RDDs
http://stackoverflow.com/questions/29284095/which-operations-preserve-rdd-order

----

Sample RDD element:
[(u'Now', u'is'), [(u'a', 1), (u'it', 3), (u'the', 9)...]),
  ...]

Sample output: 
No. know this is true, my lord. Sweet peace conduct his sweet favour. 
But now see our learning likewise is; 
'''

from pyspark import SparkContext
sc = SparkContext()

def is_not_a_number(w):
    # returns True if word is NOT a number
    try:
        for i in range(len(w)):
            temp = int(w[i])
    except:
        return True
    
    return False

def is_not_all_capitals(w):
    # returns True if word is NOT only capital letters
    # does not matter if word is followed by a period
    
    temp = w
    
    # remove possible period at the end of the word
    if temp[-1] == ".":
        temp = temp[:-1]
        
    for i in range(len(temp)):
        if w[i]<"A" or w[i]>"Z":
            return True
    
    return False

def is_not_a_unicode_marker(w):
    # returns True if word is NOT an opening file marker
    # the marker '\ufeff' may appear in files resaved in
    # unicode format
    if w == "\ufeff":
        return False
    else:
        return True

####################
#
# process words in dictionary
#
####################

# download file as one long string
whole_text = sc.textFile("Shakespeare.txt").flatMap(lambda line: line.split())

# filter out cases, and then store each word with a generated index in a tuple
filtered_set = whole_text.filter(lambda word: is_not_a_number(word) and 
                                              is_not_all_capitals(word) and
                                              is_not_a_unicode_marker(word))
filtered_set = filtered_set.zipWithIndex().cache()  # each tuple is (word, index)

####################
#
# create RDD storing ordered triplets
#
####################

# From a list of (word, index) pairs, generate ordered triplet comprising words
# with consecutive indices. 
# e.g. input:  [...(word1, 1), (word2, 2), (word3, 3), (word4, 4)...] -->
#      output: [...((word1, word2), word3), ((word2, word3), word4), ...]

rev_tuple = filtered_set.map(lambda (i, j): (j, i))
rev_shift1 = rev_tuple.map(lambda (i, j): (i+1, j))
rev_shift2 = rev_shift1.map(lambda (i, j): (i+1,j))
triplet = rev_shift2.join(rev_shift1).join(rev_tuple)
triplet = triplet.sortByKey(ascending = True).values().cache()  # remove index
filtered_set.unpersist()

####################
#
# generate RDD with all third words following (word1, word2),
# along with count in a list
#
####################

# append value of 1 to third element and 
# move third element temporarily as part of key to facilitate counting
add_cnt = triplet.map(lambda (i, j): ((i, j), 1))

# count all element with same triplet
sum_cnt = add_cnt.reduceByKey(lambda a, b: a + b)
pair_w3_cnt = sum_cnt.map(lambda ((dbl, w3), c): (dbl, (w3, c)))
phrase_list = pair_w3_cnt.groupByKey().mapValues(list)
phrase_list = phrase_list.sortByKey(ascending = True).cache()
triplet.unpersist()

########################################
########################################
#
# script to generate text from model of triplets with counts
#
########################################

'''
We could have put the code below in a different script and pass in the 
triplets RDD (e.g. phrase_list from above), to separate the tasks of
building the model, and extracting information from the model.

Accordingly, we defined the helper functions used in this section separately
here to facilitate separation if desired.
'''

def get_best_word(dict, stuple):

    '''Given a tuple (string1, string2), return a third word based on 
    selection algorithm.

    Inputs:
    dict - An RDD with elements of the form 
           (Word1, Word2), [(Word3a, Count3a), (Word3b, Count3b), ...]
           where words are strings and counts are integers.
    stuple - A tuple of the form (string1, string2) to look up in dict.

    Output:
    A string selected from Word3a, Word3b, ... based on count, according 
    to a specified algorithm. In the current implementation, we select the
    word with the maximum count; in the case of a tie, the word that appears
    first in the RDD list is chosen. 
    '''

    temp = dict.lookup(stuple) # returns list of list if there are words
    
    if temp == []:
        return None 
    temp = temp[0]  # extracts list of (word3, count) elements
    
    best_word, best_word_count = "", 0
    
    for elem in temp:
        if best_word == "":
            best_word, best_word_count = elem[0], elem[1]  # first element
        else:
            # this only replaces the current best word if the next word 
            # has a strictly higher count, based on order of elements in 
            # the phrase list; note if there is a tie, no change is made.
            # we could implement a strategy that deals with ties (e.g. random
            # selection, alphabetical order, etc.) but not done here
            if elem[1] > best_word_count:
                best_word = elem[0]
                    
    return best_word

def build_phrase(dict, stuple, length):

    '''Given a tuple (string1, string2), return a phrase of N = length words.

    Inputs:
    dict - An RDD with elements of the form 
           (Word1, Word2), [(Word3a, Count3a), (Word3b, Count3b), ...]
           where words are strings and counts are integers.
    stuple - A tuple of the form (string1, string2) to start phrase.
    length - The desired length of the phrase.

    Output:
    A string consisting of N words (if it can be built), starting with the
    given tuple.
    '''

    temp = dict.lookup(stuple) ## gets list of list 
    if temp == []:
        return None
    
    phrase = [stuple[0], stuple[1]]
    
    for i in range(length - 2):
        search_term = (phrase[i], phrase[i+1])
        word = get_best_word(dict, search_term)
        phrase.append(word)

    # We convert phrase from a list to a string.
    s = "".encode("UTF-8")
    for w in range(len(phrase)):
        s = s + phrase[w].encode("UTF-8") + " ".encode("UTF-8")
    s = s + "\n".encode("UTF-8")
    
    return s

####################
#
# generate desired number of phrases
#
####################

N_phrases = 10
words_per_phrase = 20
model_RDD = phrase_list

for i in range(N_phrases):
    # note takeSample returns a list of tuple-list pairs within a tuple
    print build_phrase(model_RDD,
                       model_RDD.takeSample(False, 1, seed=i*i)[0][0],
                       words_per_phrase)

####################
#
# write to file if desired
#
# with open('P6.txt', 'w') as f:
#    for i in range(N_phrases):
#        f.write(build_phrase(model_RDD,
#                       model_RDD.takeSample(False, 1, seed=i*i)[0][0],
#                       words_per_phrase))
# f.closed
#
####################

'''
Output:
No. know this is true, my lord. Sweet peace conduct his sweet favour. 
But now see our learning likewise is; 
large your Grace To be call'd the Quip Modest. If again it was thy joy, 
Be barr'd his entrance here. 
noise goes, this: there is but my heart is in the chase, And climb the 
highest promontory top. And have 
[...]
'''
