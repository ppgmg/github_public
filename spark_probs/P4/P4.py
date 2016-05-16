# P4.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 4 (graph generation)
#
####################

'''
This program takes a file representing Marvel character data and generates
a graph that reflects character relationships.

Each line in the file contains a "Character Name" and "Comic Issue" pair. 
In our graph representation, each character represents a node, and an edge
between two nodes means that both characters appeared in the same comic issue.
This is a symmetric graph as both characters are linked to each other.

Input: a csv file containing a pair of strings (character name, issue name)
Output: 
    chars.txt: file containing a character ID (integer) and name (string)
               on each line (space delimited)
    edges.txt: file containing a first character ID (integer) and a second
               character ID (integer) on each line representing nodes 
               connected by an edge (one edge per line, space delimited) 

Text file (comics.csv) must be in the current directory.

Note re: P4.py and P4_bfs.py

(Please also see P4.txt). We chose to structure our code in such away to
allow for greater portability: rather than having P4.py call P4_bfs.py and
pass live RDDs, Spark contexts, and potentially other parameters in an
invocation (which also typically means P4.py must be called immediately
before P4_bfs.py and therefore they might not be easily run as separate
progams), we decided to have P4.py create a text file as output
corresponding to each of the vertex and edge tables, respectively. This
allows P4_bfs.py to read the graph data at a later time. It also allows
other applications (e.g. GraphX) to use the graph data we have generated.

----

Sample input (from csv file):
"FROST, CARMILLA","AA2 35"
"KILLRAVEN/JONATHAN R","AA2 35"
"M'SHULLA","AA2 35"
"24-HOUR MAN/EMMANUEL","AA2 35"
"OLD SKULL","AA2 35"
"G'RATH","AA2 35"
"3-D MAN/CHARLES CHAN","M/PRM 35"
"3-D MAN/CHARLES CHAN","M/PRM 36"

Sample output (chars.txt):
0 "PHARAOH RAMA-TUT"
1 "GORILLA-MAN"
2 "WASP/JANET VAN DYNE"
3 "24-HOUR MAN/EMMANUEL"
4 "HUMAN ROBOT"
5 "KILLRAVEN/JONATHAN R"

Sample output (edges.txt):
13 15
15 17
13 16
4 0
14 9
13 17
17 8
1 0
7 16
12 16 

'''

from pyspark import SparkContext
sc = SparkContext()

def gen_edges(char_list):
    '''Given a list of elements, generate all two-element combinations.

    Notes: 
    This function is primarily for generating bi-directional edges on 
    a graph on which a search will be performed. Therefore:
    1. (a, b) is considered equivalent to (b, a) so is only counted once
    2. We do not count edges (self, self). 

    Input: List of elements
    Output: List of tuples

    Example:
    gen_edges(["a", "b", "c", "d"])
    [('a', 'b'), ('a', 'c'), ('a', 'd'), ('b', 'c'), ('b', 'd'), ('c', 'd')]
    '''
    
    num_char = len(char_list)
    if num_char <= 1:
        # one of fewer elements in list, so no edges
        return []
    
    edge_list = []
    for i in range(num_char):
        for j in range(i+1, num_char):
            # remove if to allow edge from self to self
            if char_list[i] != char_list[j]:
                edge_list.append((char_list[i], char_list[j])) # append tuple
    
    return edge_list


####################
#
# process input file
#
####################

lines = sc.textFile("comics.csv")
temp = lines.map(lambda line: line.split('","'))
temp = temp.map(lambda (a, b): (a[1:], b[:-1])) # tuple of strings (no quotes)

'''
We strip padded spaces on ends of names, if such padding exists.
IMPORTANT: there could be other cleaning data techniques that we 
could, to check if there are variations (e.g. in case, spacing, 
extra punctuation, etc.) that should be mapped to the same
character. However, given my lack of knowledge of this domain, 
we used the character and issue names on an "as-is" basis (except 
for stripping padded spaces at the beginning/end of strings). 
Additional cleaning of the data may lead to different results.
'''
data = temp.map(lambda (x ,y): (x.strip(), y.strip())).cache()

####################
#
# Build vertex table (index in alphabetical order)
#
####################

chars = data.map(lambda (x, y): x).distinct()
chars_sort = chars.map(lambda x: (x, 1)).sortByKey(ascending = True)
chars_new_index = chars_sort.map(lambda (x, y): x).zipWithIndex()

vertex_table = chars_new_index.map(lambda (x, y): (y, x)).cache()  #(index, name)

# use broadcast table (value has list of index, name tuples) for quick lookups
# and provide helper function, used for generating edge table

lookup_table = sc.broadcast(vertex_table.collect())

def get_char_ID(s):
    # get character ID given the name
    for i in range(len(lookup_table.value)):
        if lookup_table.value[i][1] == s:
            return lookup_table.value[i][0]

####################
#
# Build edge table (sorted by character ID)
#
####################

# create list of characters by issue
rev_data = data.map(lambda (x, y): (y, x))  # (comic issue, character name)
chars_by_issue = rev_data.groupByKey().mapValues(list)

# expand character list
expand_list = chars_by_issue.flatMap(lambda (x, y): gen_edges(y))

# treat link from a->b the same as b->a (symmetric graph)
# we can remove this filtering if we want to treat edges as directed
order_nodes = expand_list.map(lambda (x, y): (x, y) if x < y else (y, x)).distinct()
node_index = order_nodes.map(lambda (x, y): (get_char_ID(x), get_char_ID(y)))

edge_table = node_index.sortByKey(ascending = True).cache()


####################
#
# write data in graph RDDs to disk
#
####################

# vertex_table and edge_table can also be passed onto other functions as RDDs
# however, here we write the data into files in the working directory

with open('chars.txt', "w") as f:
    for i in range(len(lookup_table.value)):
        f.write('%d' % lookup_table.value[i][0])
        f.write('%s' % ' "' + lookup_table.value[i][1].encode("UTF-8") + '"\n')
f.closed

edge_data = edge_table.collect()
with open('edges.txt', "w") as f:
    for i in range(len(edge_data)):
        f.write('%d' % edge_data[i][0])
        f.write('%s' % ' ')
        f.write('%d' % edge_data[i][1])
        f.write('%s' % '\n')
f.closed