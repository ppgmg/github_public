# P5_bfs.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 5 (Shortest Path)
#
####################

'''
This program takes as input graph data with directed links, and performs
a breadth first search (BFS) to reports the shortest path between two nodes.

Driver code to allow for the loading of data from an example set of vertex and 
edge files has also been provided. Assumes files for links-simple-sorted.txt
and titles-sorted.txt are in current working directory (or can modify filenames
below - e.g. "s3://....."). Can also increase numParts to set the number of
partitions for running the program on different machines.

IMPORTANT: The page names (and links) used in the example are 1-indexed.

----

Sample input for driver (titles-sorted.txt):
...
Kevin_Allin
Kevin_Allison
Kevin_Altieri
Kevin_Alves
Kevin_Amankwaah
Kevin_Ambler
Kevin_Amuneke
Kevin_Amunike
...

Sample input for driver (links-simple-sorted.txt):
1: 1664968
2: 3 747213 1664968 1691047 4095634 5535664

Sample output from an invocation of find_path:
find_path(src_name, dest_name, sc, char_table, edge_table)
stage:  1
queue length:  1
unsearched graph size:  130160392
stage:  2
queue length:  225
unsearched graph size:  130160167
[u'Kevin_Bacon', u'College_Bowl', u'Harvard_University']

'''

from pyspark import SparkContext
sc = SparkContext()

vertex_file = "titles-sorted.txt"  # one string per line (1 - indexed)
edge_file = "links-simple-sorted.txt"  # format src: dest dest dest ...

numParts = 8  # number of partitions to be used

def gen_graph_RDD(vfile, efile, sc):

    '''Generate vertex and edge RDDs from files.

    Can be skipped if data is already loaded in RDDs.

    Input:  vfile - filename of vertex data (one string per line, 1-indexed)
                    (no quotes)
            efile - filename of edge data 
                    (file records are of the form: src: dest dest ...)
                    (also 1-indexed)
            sc - SparkContext

    Output: char_RDD - vertex data in a RDD
            edge_RDD - edge data in a RDD (as src node, dest node pairs)
    '''

    lines = sc.textFile(vfile)
    char_RDD = lines.zipWithIndex().map(lambda (x, y): (y + 1, x)) # 1-index

    lines = sc.textFile(efile)
    edge_elems = lines.map(lambda line: line.split(' '))
    separate_src = edge_elems.map(lambda x: (int(x[0][:-1]), (x[1:])))
    flattened = separate_src.flatMapValues(lambda x: x)  # edge table representation
    edge_RDD = flattened.mapValues(int) 

    return char_RDD, edge_RDD

def number_for(char_RDD, char_name):
    '''Retrieve ID corresponding to char_name'''
    id = char_RDD.map(lambda (x, y):(y, x)).lookup(char_name)
    if id == []:
        return -1
    else:
        return id[0]

def name_for(char_RDD, char_index):
    '''Retrieve name corresponding to char_index'''
    name = char_RDD.lookup(char_index)
    if name == []:
        return "unknown"
    else:
        return name[0]

def copartitioned(RDD1, RDD2):
    '''check if two RDDs are copartitioned'''
    return RDD1.partitioner == RDD2.partitioner

####################
#
# search for shortest path
#
####################

def find_path(s, d, sc, char_RDD, fw_edges, rev_edges=[]):
    '''Given two page names in char_RDD, and edge RDDs, output shortest path
between two pages.

    Notes: 

    We are assume uni-directional links. That is, link from A to B does not
    imply a link from B to A.

    Can silence message by setting progress_messages_on = False.

    We are using the global variable numParts.

    Input: s - a string representing a Wiki page where path begins
           d - a string representing a Wiki page where path ends
           sc - SparkContext
           char_RDD - RDD of (int, string) pairs -- i.e. pageID, page name
           fw_edges - RDD of (int, int) pairs, representing nodes 
                      (with IDs from char_RDD) connected by edges

    Output: print out a shortest path

    Example (progress_messages_on = True):
    Finding path from: Kevin_Bacon to Harvard_University
    stage:  1
    queue length:  1
    unsearched graph size:  130160392
    stage:  2
    queue length:  225
    unsearched graph size:  130160167
    [u'Kevin_Bacon', u'College_Bowl', u'Harvard_University']
    '''
    
    global numParts
    progress_messages_on = True

    ## get IDs for source and target nodes
    root = number_for(char_RDD, s)
    if root < 1:  # should not be a 0-index either
        raise ValueError('invalid source page')

    target = number_for(char_RDD, d)
    if target < 1:
        raise ValueError('invalid destination page')

    ## check for trivial case
        if root == target:
            print "%s %s" % ("Shortest Path: ", name_for(root))
            return

    # ensure input rdds are partitioned
    char_RDD = char_RDD.partitionBy(numParts).cache()
    fw_edges = fw_edges.partitionBy(numParts).cache()

    # setup rdd to store distances and parent node ID for path traceback
    # (character ID, (distance from 0th level node, parent node ID)
    # initialize distances from source to zero, all others to infinity
    # initialize parent node IDs to none
    distances = char_RDD.map(lambda (indx, name): 
                              (indx, (0, None)) if indx==root 
                                  else (indx, (float("inf"), None)),
                               preservesPartitioning=True)

    # initialize queue: start with source node as root (stage 0)
    # queue elements are tuples of ints (node to search on, current search stage)
    my_queue = sc.parallelize([(root, 0)]).partitionBy(numParts).cache()

    # set accumulators, loop until queue is empty, stage is used to track progress
    stage = sc.accumulator(0)
    total_edges = fw_edges.count()
    unsearched_links = sc.accumulator(total_edges)
    # total_nodes = char_RDD.count()  # can use for debugging or reporting
    # untouched_nodes = sc.accumulator(total_nodes - 1)  # can use for debugging

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
        fw_srch = my_queue.join(fw_edges)
        unsearched_links += -fw_srch.count()

        # create new edge table that does not include current node(s) as source
        # i.e. separate edges we will not traverse for use in next iteration
        # cache it as we will use it as our new edge table in next stage
        fw_edges = fw_edges.subtractByKey(my_queue, numParts).cache()

        # map potential destination node as new key, current stage k is stored
        # in tuple as value with the source node saved
        fw_srch_dests = fw_srch.map(lambda (src, (k, dest)): (dest, (k, src)))

        # merge two lists and keep unique keys
        # in theory, we may reach the same node via two different paths
        # it makes no difference to the length of the path since we are on the same
        # stage of the BFS - since we have no requirement to save information for *all*
        # parent nodes (we need only one shortest path), we arbitrarily keep the 
        # destination node paired with the parent node having the * minimum * ID. 
        # Alternative implementations could employ some other strategy for choosing 
        # the 'official' parent node, or modify the code to store all parent nodes.
        # possible_dests are in the form tuples (dest, (k, src))
        possible_dests = fw_srch_dests.reduceByKey(min, numPartitions=numParts)

        # join with existing distance table: old value will be extracted as oldk
        #     Note: after leftOuterJoin, for nodes in possible_dests list
        #     dist_search elements will be (dest, ((oldk, old_par), (k, par)));
        #     for nodes not in possible_dests list, dist_search element
        #     will be in the format (dest, ((oldk, old_par), None))
        # check partitioning for efficient join
        assert copartitioned(distances, possible_dests) 
        dist_search = distances.leftOuterJoin(possible_dests)

        # update queue with next nodes to be searched, cache for next iteration
        # only include nodes not previously visited to continue search
        # (unvisited nodes have oldk_par[0] = "inf")
        # _tup denotes a tuple
        # queue only requires stage value to be stored with nodeID to be searched
        # parent value will be stored only in the distance table (see below)
        new_dests = dist_search.filter(lambda (dest, (oldk_par_tup, k_par_tup)): 
                            k_par_tup != None and k_par_tup[0] < oldk_par_tup[0])
        my_queue = new_dests.mapValues(lambda (oldk_par_tup, k_par_tup): k_par_tup[0])
        my_queue = my_queue.cache()

        # update distance table storing (stage, parent) tuple info for only 
        # the now-visited nodes; cache table for next iteration
        # untouched_nodes += -my_queue.count()  # can use for debugging or reporting
        distances = dist_search.mapValues(lambda (oldk_par_tup, k_par_tup):
                                    k_par_tup if k_par_tup != None and 
                                                  k_par_tup[0] < oldk_par_tup[0] 
                                              else oldk_par_tup)
        distances = distances.cache()

        # check if target node has been found
        # We may have checked for the destination after the initial join: that
        # may cause us to exit the loop quicker but it would require us to search
        # through a potentially much longer list.
 
        found = my_queue.filter(lambda (dest, k): dest == target)
        if found.count() > 0:
            break

    # check if we found a path, if so print it out
    # do this by checking entry for parent node corresponding to 
    # target ID in distances table
    table = distances.collectAsMap()
    if table[target][1] == None:
        print "No path found"
    else:
        # generate path as output (trace back through nodes visited)
        # if paths are expected to be long, we could consider broadcasting
        # a map with the page name elements (i.e. char_RDD) to make name lookups
        # more efficient (but they seemed short, and we need not lookup endpoints)
        path_list = [d]
        trace_pointer = target
        while table[trace_pointer][1] != root:
            path_list = [name_for(char_RDD, table[trace_pointer][1])] + path_list
            trace_pointer = table[trace_pointer][1]
        assert table[trace_pointer][1] == root
        path_list = [s] + path_list
        print path_list    

    return   


####################
#
# main
#
####################

# generate RDDs for vertices and edges from file
# can skip if char_table, edge_table can be assigned to existing/imported RDDS
print "loading data..."
char_table, edge_table = gen_graph_RDD(vertex_file, edge_file, sc)
char_table.cache()
edge_table.cache()

# define source and destination
endpoints_list = [("Kevin_Bacon", "Harvard_University"), 
                  ("Harvard_University", "Kevin_Bacon")]

for node_pair in endpoints_list:
    print "%s %s %s %s" % ("Finding path from:", node_pair[0], "to", node_pair[1])
    find_path(node_pair[0], node_pair[1], sc, char_table, edge_table)
    print "\n"
