# P3.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 3
#
####################

'''
This program takes a file of words and generates an RDD, with elements comprising:
1. a sequence of letters in alphabetical order, distinct from all other sequences
2. the number of valid anagrams, occurring in the same input file
3. a list containing all such valid anagrams

The program will also extract and output the line from this RDD with the largest
number of anagrams.

Note: Dictionary file (EOWL_words.txt) must be in the current directory.

----

Sample Input:
bath
hep
are
era
ear
timex
peh
bhat
bah
ba

Sample RDD (using `collect()`):
[(u'ab', 1, [u'ba']),
 (u'abh', 1, [u'bah']),
 (u'abht', 2, [u'bath', u'bhat']),
 (u'aer', 3, [u'are', u'era', u'ear']),
 (u'ehp', 2, [u'hep', u'peh']),
 (u'eimtx', 1, [u'timex'])]

Sample output: 
(u'aer', 3, [u'are', u'era', u'ear'])
'''

from pyspark import SparkContext
sc = SparkContext()

def sortletters(s):
    # sort characters of a string in place
    return "".join(sorted(s))

####################
#
# process words in dictionary
#
####################

lines = sc.textFile("EOWL_words.txt")

# we are converting all letters to lower case
# if it is desirable to keep capital letters as unique from their lower-case
# counterparts, the line below can be removed
# also, all words should already be unique (as it is a dictionary), but we 
# apply the distinct transformation in case they are not
lines = lines.map(lambda word: word.lower()).distinct()

####################
#
# generate anagram list
#
####################

# generate (key, value) pair based on word, where the key is the sorted 
# letter sequence and the value is the original word
let_sequence = lines.map(lambda word: (sortletters(word), word))

# group elements by the key, with all values with same key put into a list 
# then sort letter sequences
anagram_list = let_sequence.groupByKey().mapValues(list)
sorted_seq = anagram_list.sortByKey(ascending = True)

####################
#
# prepare output
#
####################

# add, as second element of RDD, the count of the number of anagrams
# for each letter sequence in key; each element in RDD takes the form of
# (letter sequence, number of anagrams, [word1, word2, word3,...]) 
list_with_count = sorted_seq.map(lambda (ls, list_anags): (ls, 
                                                           len(list_anags), 
                                                           list_anags))
# list_with_count.collect() # can uncomment to view RDD contents

# sort RDD by number of anagrams in decreasing order, and extract top result 
# (most anagrams)
N = 1  # number of top entries desired
top_entries = list_with_count.takeOrdered(N, key = lambda x: -x[1])
print top_entries[0]  # extract element from RDD for printing

####################
#
# to write result to a file
#
# with open('P3.txt', 'w') as f:
#    f.write(str(top_entries[0]))
# f.closed
#
####################

"""
Output:
(u'aelst', 11, [u'salet', u'steal', u'stela', u'tesla', u'stale', u'taels', 
	u'slate', u'teals', u'tales', u'least', u'leats'])
"""
