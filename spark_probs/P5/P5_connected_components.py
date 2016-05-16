# P5_connected_components.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 5 (Connected Components)
#
####################

'''
This program takes as input graph data, and determines the number of connected
components.

Driver code to allow for the loading of data from an example set of vertex and 
edge files has also been provided. Assumes files for links-simple-sorted.txt
and titles-sorted.txt are in current working directory (or can modify filenames
below - e.g. "s3://....."). Can also increase numParts to set the number of
partitions for running the program on different machines.

Note the flag `links_symmetric` can be set to identify whether each link in the
graph is to be taken as symmetric (links_symmetric = True) or whether two nodes
A and B are only considered symmetric if there is both a link from A to B and a
link from B to A given. 

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

Sample output from an invocation of find_all_ccs:
find_all_ccs(sc, char_table, edge_table)
total clusters:  88
biggest cluster (clusterID, size):  (5, 5)

'''

from pyspark import SparkContext
sc = SparkContext()

vertex_file = "s3://Harvard-CS205/wikipedia/titles-sorted.txt"
edge_file = "s3://Harvard-CS205/wikipedia/links-simple-sorted.txt"

numParts = 128  # number of partitions to be used

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
# search for all connected components
#
####################

def find_all_ccs(sc, char_RDD, fw_edges):
    '''Calculates the number of connected components in a graph, and outputs the
largest number.

    Notes: 

    We implemented a flag called `links_symmetric` that can be set to
    identify whether each link in the graph is to be taken as symmetric 
    (links_symmetric = True) or whether two nodes A and B are only considered 
    symmetric if there is both a link from A to B and a link from B to A given. 

    Can silence message by setting progress_messages_on = False.

    We are using the global variable numParts.

    Input: s - a string representing a Wiki page where path begins
           d - a string representing a Wiki page where path ends
           sc - SparkContext
           char_RDD - RDD of (int, string) pairs -- i.e. pageID, page name
           fw_edges - RDD of (int, int) pairs, representing nodes 
                      (with IDs from char_RDD) connected by edges

    Output: print out number of connected components and size of largest one

    Example (progress_messages_on = False):
    total clusters:  88
    biggest cluster (clusterID, size):  (5, 5)
    '''
    
    global numParts
    progress_messages_on = True
    links_symmetric = True

    # ensure input rdds are partitioned
    char_RDD = char_RDD.partitionBy(numParts).cache()
    fw_edges = fw_edges.partitionBy(numParts).cache()

    # generate second edge table with elements reversed if links in edge_table
    # are to be treated as symmetric
    rev_edges = fw_edges.map(lambda (x, y): (y, x))
    rev_edges = rev_edges.sortByKey().partitionBy(numParts).cache()

    if not links_symmetric:
        # check if this flag has been set
        # if we are to assume nodes are linked only if they link to each other,
        # this means that the same link should appear in both the 
        # (forward) and reverse edge tables  
        # e.g. A->B and B->A are in edge_table, 
        #          both B->A and A->B will be in rev_edge_table
        #      C->D with no D->C, 
        #          C->D appears in edge_table but will not appear in rev_edge_table
        # we can thus take the intersection and work only with links 
        # found to be bidirectional, and replace our working edge table
        fw_edges = fw_edges.intersection(rev_edges).partitionBy(numParts).cache()
        # clear reverse link table, all links now in main table
        rev_edges = sc.parallelize([]).partitionBy(numParts).cache()  

    # setup rdd to store cluster numbers (indexed by page)
    # initialize cluster number to infinity, except root node
    # we arbitrarilty start with root node = 1
    # wWe used the hash of the lowest node ID in the cluster as
    # the cluster number.
    root = 1 
    clusters = char_RDD.map(lambda (indx, name): 
                              (indx, hash(root)) if indx==root 
                                                    else (indx, float("inf")),
                               preservesPartitioning=True)

    # initialize queue: start with source node as root
    # queue elements are tuples of ints (node to search on, current cluster)
    my_queue = sc.parallelize([(root, hash(root))]).partitionBy(numParts).cache()

    # set accumulators, stage is used to track progress
    # stage = sc.accumulator(0)  # internal stage, can use for debugging or reporting
    cluster_number = sc.accumulator(1)
    total_edges = fw_edges.count() + rev_edges.count()
    unsearched_links = sc.accumulator(total_edges)
    total_nodes = char_RDD.count()  
    untouched_nodes = sc.accumulator(total_nodes - 1)

    ##########
    # loop while there are still edges to explore
    ##########
    # note if all edges have been explored but node has not yet been visited;
    # it is an isolated vertex, and clusters table will still have an "inf" value 
    # stored for that node
    ##########

    if progress_messages_on:
        print "%s %d" % ("--- building cluster --- ", cluster_number.value)
        print "%s %d" % ("unvisited nodes: ", untouched_nodes.value)

    while unsearched_links.value>0:

        # update internal stage (if desired for debuggin)
        # stage += 1

        # can also set for extra information on internal stages (each BFS)
        # if progress_messages_on:         
            # print "%s %d" % ("stage: ", stage.value)
            # print "%s %d" % ("queue length: ", my_queue.count())
            # print "%s %d" % ("unsearched graph size: ", unsearched_links.value)
            # print "%s %d" % ("unvisited nodes: ", untouched_nodes.value)

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

        # map potential destination node as new key, current cluster k as value
        # we no longer need the source node in this implementation
        fw_srch_dests = fw_srch.map(lambda (src, (k, dest)): (dest, k))
        rev_srch_dests = rev_srch.map(lambda (src, (k, dest)): (dest, k))

        # merge two lists and keep unique keys (all values already equal k)
        # possible_dests are in the form tuples (dest, k)
        merge = fw_srch_dests.union(rev_srch_dests)
        possible_dests = merge.reduceByKey(lambda x, y: x, 
                                              numPartitions=numParts)

        # join with existing clusters table: old value will be extracted as oldk
        #     Note: after leftOuterJoin, for nodes in possible_dests list
        #     c_search elements will be (dest, (oldk, k)));
        #     for nodes not in possible_dests list, c_search element
        #     will be in the format (dest, (oldk, None))
        # check partitioning for efficient join
        assert copartitioned(clusters, possible_dests)      
        c_search = clusters.leftOuterJoin(possible_dests)

        # update queue with next nodes to be searched, cache for next iteration
        # only include nodes not previously visited to continue search
        # (unvisited nodes have oldk = "inf")
        new_dests = c_search.filter(lambda (dest, (oldk, k)): 
                                             k != None and oldk==float("inf"))
        my_queue = new_dests.mapValues(lambda (oldk, k): k).cache()

        # also update cluster table storing current k for the now-visited nodes
        # cache for next iteration
        untouched_nodes += -my_queue.count()
        clusters = c_search.mapValues(lambda (oldk, k):
                                       k if k != None and oldk==float("inf") 
                                             else oldk).cache()

        # check if current queue is empty 
        # (i.e. all nodes for this cluster has been found)
        # if all nodes have been visited, we are done
        # otherwise, repopulate queue with a new node, one that has not 
        # yet been assigned a cluster (we choose the unassigned node with
        # the minimum ID)
        # we can use the hash of the charID of the first element of the cluster 
        # as a unique cluster ID
 
        if untouched_nodes.value==0:
            break

        if my_queue.count()==0:
            # get next `root` to find next cluster
            nodesleft = clusters.filter(lambda (node, k): k==float("inf"))
            new_min_root = nodesleft.map(lambda (x,y): x).min()
            # reset queue and cache for next iteration
            # stage = sc.accumulator(0)
            my_queue = sc.parallelize([(new_min_root, hash(new_min_root))])
            my_queue = my_queue.partitionBy(numParts).persist()
            # update clusters table with cluster number for new root
            # cache for next iteration
            clusters = clusters.map(lambda (indx, c): 
                            (indx, hash(new_min_root)) if indx==new_min_root 
                                else (indx, c), preservesPartitioning=True) 
            clusters = clusters.persist()

            untouched_nodes += -1
            if progress_messages_on:
                cluster_number += 1
                print "%s %d" % ("--- building cluster --- ", 
                                  cluster_number.value)
                print "%s %d" % ("unvisited nodes: ", untouched_nodes.value)

        assert my_queue.count() > 0

    ###########
    # print out summary information of collected components
    ###########
    # note the final cluster RDD will have stored (node ID, cluster number)
    # we can choose to pull all nodes belonging to a cluster if desired
    # and/or call helper functions provided to determine names
    # associated with IDs
    ###########

    # generate structure to store (cluster ID, node count); 
    # assign orphans (i.e. unvisited nodes) a cluster ID
    assign_count = clusters.map(lambda (x, y): (y ,1) if y != float("inf") 
                                                          else (hash(x), 1))
    cluster_count = assign_count.reduceByKey(lambda x, y : x + y)
    # get size of largest cluster
    max_cluster_info = cluster_count.takeOrdered(1, lambda kv: -kv[1])
    
    print "\n"
    print "%s %d" % ("total clusters: ", cluster_count.count())
    print "%s %s" % ("biggest cluster (cluster ID, size): ", str(max_cluster_info[0]))  

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

print "Finding number of connected components"
find_all_ccs(sc, char_table, edge_table)

