# P4_bfs.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 4 (BFS)
#
####################

'''
This program provide a function that takes as input graph data and performs
a breadth first search (BFS) for all connected components from a source node.
Output indicates number of touched nodes (including source).

Driver code to allow for the loading of data from an example set of vertex and 
edge files has also been provided. Assumes chars.txt and edges.txt are files
in current working directory.

----

Sample input for driver (chars.txt):
0 "PHARAOH RAMA-TUT"
1 "GORILLA-MAN"
2 "WASP/JANET VAN DYNE"
3 "24-HOUR MAN/EMMANUEL"
4 "HUMAN ROBOT"
5 "KILLRAVEN/JONATHAN R"

Sample input for driver (edges.txt):
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

Sample output from an invocation of BFS:
BFS(char_name, sc, char_table, edge_table, rev_edge_table)
<...progress messages...>
unvisited:  36
visited:    6403

'''

from pyspark import SparkContext
sc = SparkContext()

vertex_file = "chars.txt"  # space-delimited int/"string" pairs
edge_file = "edges.txt"  # space-delimited int/int pairs

numParts = 8  # number of partitions to be used

def gen_graph_RDD(vfile, efile, sc):

    '''Generate vertex and edge RDDs from files.

    Can be skipped if data is already loaded in RDDs.

    Input:  vfile - filename of vertex data (string)
                    (file records are of the form: int "<string>")
            efile - filename of edge data (string)
                    (file records are of the form: int int)
            sc - SparkContext

    Output: char_RDD - vertex data in a RDD
            edge_RDD - edge data in a RDD
    '''

    lines = sc.textFile(vfile)
    char_RDD = lines.map(lambda line: line.split(' "')) \
                   .map(lambda (x, y): (int(x), y[:-1]))

    lines = sc.textFile(efile)
    edge_RDD = lines.map(lambda line: line.split(' '))  \
                   .map(lambda (x, y): (int(x), int(y)))

    return char_RDD, edge_RDD

def number_for(char_RDD, char_name):
    '''Retrieve ID corresponding to char_name'''
    id = char_RDD.map(lambda (x, y):(y, x)).lookup(char_name)
    if id == []:
        return -1
    else:
        return id[0]

def copartitioned(RDD1, RDD2):
    '''check if two RDDs are copartitioned'''
    return RDD1.partitioner == RDD2.partitioner

####################
#
# BFS search function
#
####################

def BFS(s, sc, char_RDD, fw_edges):
    '''Given a character name in char_RDD, and edge RDDs, output number of
touched nodes.

    Notes: 

    Can silence message by setting progress_messages_on = False.

    We are using the global variable numParts.

    Input: s - a string representing a character name
           sc - SparkContext
           char_RDD - RDD of (int, string) pairs
           fw_edges - RDD of (int, int) pairs, representing nodes 
                      (with IDs from char_RDD) connected by edges

    Output: print out visited and unvisited nodes

    Example (progress_messages_on = True):
    CAPTAIN AMERICA
    stage:  1
    queue length:  1
    unsearched graph size:  334200
    stage:  2
    queue length:  1903
    unsearched graph size:  332297
    stage:  3
    queue length:  4461
    unsearched graph size:  98293
    stage:  4
    queue length:  38
    unsearched graph size:  261
    unvisited:  36
    visited:    6403
    '''
    
    global numParts
    progress_messages_on = True

    ## get ID for source node
    root = number_for(char_RDD, s)
    if root < 0:
        raise ValueError('character not found')

    # ensure input rdds are partitioned
    char_RDD = char_RDD.partitionBy(numParts).cache()
    fw_edges = fw_edges.partitionBy(numParts).cache()

    # generate second edge table with elements reversed, links in edge_table
    # are to be treated as symmetric
    rev_edges = fw_edges.map(lambda (x, y): (y, x))
    rev_edges = rev_edges.sortByKey().partitionBy(numParts).cache()

    # setup rdd to store distances (character ID, distance from 0th level node)
    # initialize distances from source to zero, all others to infinity
    distances = char_RDD.map(lambda (indx, name): 
                              (indx, 0) if indx==root else (indx, float("inf")),
                               preservesPartitioning=True)

    # initialize queue: start with source node as root (stage 0)
    # queue elements are tuples of ints (node to search on, current search stage)
    my_queue = sc.parallelize([(root, 0)]).partitionBy(numParts).cache()

    # set accumulators, loop until queue is empty, stage is used to track progress
    stage = sc.accumulator(0)
    total_edges = fw_edges.count() + rev_edges.count()
    unsearched_links = sc.accumulator(total_edges)
    total_nodes = char_RDD.count()
    untouched_nodes = sc.accumulator(total_nodes - 1)

    while my_queue.count()>0:

        # update stage
        stage += 1

        if progress_messages_on:
            print "%s %d" % ("stage: ", stage.value)
            print "%s %d" % ("queue length: ", my_queue.count())
            print "%s %d" % ("unsearched graph size: ", unsearched_links.value)

        # store current stage k for queued nodes
        my_queue = my_queue.mapValues(lambda k: k+1)

        # determine edges originating from source node
        # output: (search node, (k, destination node))
        # check partitioning for efficient join
        assert copartitioned(my_queue, fw_edges)
        assert copartitioned(my_queue, rev_edges)
        fw_srch = my_queue.join(fw_edges)
        rev_srch = my_queue.join(rev_edges)
        unsearched_links += -(fw_srch.count() + rev_srch.count())

        # create new edge tables that do not include current node(s) as source
        # i.e. separate edges we will not traverse for use in next iteration
        # cache it as we will use it as our new edge table(s) in next stage
        fw_edges = fw_edges.subtractByKey(my_queue, numParts).cache()
        rev_edges = rev_edges.subtractByKey(my_queue, numParts).cache()

        # map potential destination node as new key, current stage k as value
        # we no longer need the source node in this implementation
        fw_srch_dests = fw_srch.map(lambda (src, (k, dest)): (dest, k))
        rev_srch_dests = rev_srch.map(lambda (src, (k, dest)): (dest, k))

        # merge two lists and keep unique keys (all values already equal k)
        # possible_dests are in the form tuples (dest, k)
        merge = fw_srch_dests.union(rev_srch_dests)
        possible_dests = merge.reduceByKey(lambda x, y: x, 
                                              numPartitions=numParts)

        # join with existing distance table: old value will be extracted as oldk
        #     Note: after leftOuterJoin, for nodes in possible_dests list
        #     dist_search elements will be (dest, (oldk, k)));
        #     for nodes not in possible_dests list, dist_search element
        #     will be in the format (dest, (oldk, None))
        # check partitioning for efficient join
        assert copartitioned(distances, possible_dests)      
        dist_search = distances.leftOuterJoin(possible_dests)

        # update queue with next nodes to be searched, cache for next iteration
        # only include nodes not previously visited to continue search
        # (unvisited nodes have oldk = "inf")
        new_dests = dist_search.filter(lambda (dest, (oldk, k)): 
                                             k != None and k < oldk)
        my_queue = new_dests.mapValues(lambda (oldk, k): k).cache()

        # update distance table storing stage for only the now-visited nodes
        # cache for next iteration
        untouched_nodes += -my_queue.count()
        distances = dist_search.mapValues(lambda (oldk, k):
                                       k if k != None and k < oldk else oldk)
        distances = distances.cache()

    print "%s %d" % ("unvisited: ", untouched_nodes.value)
    print "%s %d" % ("visited:   ", total_nodes - untouched_nodes.value) 

    return       


####################
#
# main
#
####################

# generate RDDs for vertices and edges from file
# can skip if char_table, edge_table can be assigned to existing/imported RDDS
char_table, edge_table = gen_graph_RDD(vertex_file, edge_file, sc)
char_table.cache()
edge_table.cache()

# characters to search
char_list = ["CAPTAIN AMERICA", "MISS THING/MARY", "ORWELL"]

for char_name in char_list:
    print char_name
    BFS(char_name, sc, char_table, edge_table)
    print "\n"
