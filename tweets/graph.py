# graph.py

# Coding Challenge (31 Mar 2016)
# For Insight Data Engineering Application
# Kendrick Lo
# Details at: https://github.com/ppgmg/coding-challenge

import numpy as np
import json
from datetime import datetime


class Graph:
    '''A Twitter hashtag graph.

    We represent the graph using an adjacency list representation: each key in
    the `adjlists` dictionary is the hashtag (case sensitive string)
    representing a node in the graph, and the value is a set of unique hashtags
    (other nodes) to which the node is connected.

    We record the timestamp associated with each edge in the graph in a
    separate `edgetimes` dictionary, indexed by a tuple (node1, node2),
    where the value is a `datetime` object.

    IMPORTANT NOTE: due to compatability issues with Python 2, we have ignored
    the UTC offset in the timestamps. Put another way, we have assumed that the
    timestamps of all tweets have a +0000 offset. On a cursory exploration of
    the data, it appears this may be the case; however, if times could have
    different offsets, then the `_current_time` function should be modified
    (either by using a different package, or by manual adjustment), otherwise a
    new "later" tweet could inadvertently erase data for an existing graph.'''

    def __init__(self):

        self._adjlists = {}  # adjacency list graph representation
        self._edgetimes = {}  # store timestamp entries by edge (src, dst)
        self._edgeq = []  # alternate representation of edgetimes, time indexed
        self._avgdeg = 0.0  # current average degree

        self._latesttime = None  # store latest timestamp
        self._L = 60  # maximum length of window in seconds

        self._log = False  # set to True to send log messages to std output

    def process_tweet(self, tweet, log=False):
        '''Update hashtag graph using data from new tweet and return updated
        average degree of graph measured over fixed time window.

        Input:
            input_s: single tweet in JSON format
        Output:
            updated average degree of graph (float)
            returns None if error

        Note:
            Log messages are printed to standard output if `self._log` is True
        '''

        def _current_time(ts):
            # convert time in string format to a datetime object
            # assume input is in the form: "Thu Nov 05 05:05:39 +0000 2015"
            # assumes all offsets are +0000 (ignored)
            return datetime.strptime(ts[:-10]+ts[-4:], "%a %b %d %H:%M:%S %Y")

        # set logging status
        self._log = log

        # get list of unique hashtags and corresponding timestamp for tweet
        hashtags, timestamp = self._get_tags_from_tweet(tweet)
        if hashtags is None:
            return None
        now = _current_time(timestamp)

        if self._log:
            print "total nodes: %i, total edges %i" % (len(self._adjlists),
                                                       len(self._edgetimes))
            print "extracted hashtags:", hashtags, "at", timestamp

        # check if current tweet is stale, if so return existing degree value
        if ((self._latesttime is not None) and (self._latesttime > now) and
                ((self._latesttime - now).seconds > self._L)):
            if self._log:
                print self._avgdeg
            return self._avgdeg

        # check if tweet is later in time compared to other tweets in graph;
        # if so, purge old tweets
        if self._latesttime is None:
            self._latesttime = now
        if (self._latesttime is not None) and (now > self._latesttime):
            self._latesttime = now
            self._purge_old_tweets(self._L)

        # add hashtags to graph
        self._add_nodes_to_graph(hashtags, now)

        # compute average degree
        if len(self._adjlists) != 0:
            degs = [len(l) for l in self._adjlists.values()]
            self._avgdeg = np.mean(degs)
            # sum of list should equal number of edges
            assert np.sum(degs) == len(self._edgetimes) == len(self._edgeq)
        else:
            self._avgdeg = 0.0
            assert len(self._edgetimes) == 0

        if self._log:
            print self._avgdeg

        return self._avgdeg

    def _get_tags_from_tweet(self, json_tweet):
        '''Takes a tweet in JSON format as input and returns list of unique hashtags,
        with corresponding time stamp.

        Input:
            json_tweet: single tweet in JSON format
        Output:
            a python list of unique hashtags
            a string representing the time stamp for tweet

        Notes:
        a) Log messages are printed to standard output if `self._log` is True
        b) If JSON tweet was not empty and not a limit statement, an empty list
        is returned when the tweet does not contain the hashtags entity, with
        the appropriate timestamp. However, if JSON tweet was empty, was only
        a limit statement, or there was some error in processing the tweet,
        (None, None) is returned instead.'''

        try:
            tweet = json.loads(json_tweet)
            nodes = []
            timestamp = ""

            if (len(tweet) == 1) and (tweet.keys()[0] == "limit"):
                if self._log:
                    print "ignoring input: deleting limit statement"
                return None, None

            if len(tweet) == 0:
                if self._log:
                    print "ignoring input: empty tweet"
                return None, None

            for key, value in tweet.items():
                if key == "created_at":
                    timestamp = value
                # assumes there is a unique `hashtags` entry in entities, and
                # value is a dictionary
                # format of each hashtag entry is, e.g.:
                #     {u'indices': [9, 18], u'text': u'Pisteare'}
                # get the name of the hashtag from the text field
                if key == "entities":
                    nodes = [item["text"] for item in value["hashtags"]]
                    nodes = list(set(nodes))  # keep unique only
                # exit early if both timestamp and nodes list populated
                if nodes and timestamp:
                    break
        except:
            # error in extracting hashtags, ignore and continue
            if self._log:
                print "ignoring input: failed to process JSON"
            return None, None

        return nodes, timestamp

    def _add_nodes_to_graph(self, taglist, t):
        '''Takes a list of hashtag names and datetime object, and updates the
        adjacency list representation and timestamp records for the instance
        graph. Duplicate node entries are not added.

        Notes:
        (a) Log messages are printed to standard output if `self._log` is True
        (b) t is datetime object. Assume all timestamps have +0000 UTC offset.
        To accommodate other offsets, modify `_current_time`.
        (c) If there is only one hashtag (or none), no new nodes are created.
        (d) From the spec: "If multiple tweets within a 60-second window have
        the same pair of hashtags, should they be connected twice? Ans: No,
        please don't count multiple connection [...] However, you should ensure
        that the timestamp of the corresponding edge is properly updated."
          * We assume "updating the timestamp" => "keeping the later timestamp"
        '''

        if len(taglist) < 2:
            return

        for i, item in enumerate(taglist):

            others = taglist[:i] + taglist[i+1:]  # neighboring hashtags

            # update list for current item
            if item not in self._adjlists:
                # new node, link to all other nodes and record timestamp
                if self._log:
                    print "new node added for", item
                self._adjlists[item] = others
                for nbr in others:
                    self._update_times((item, nbr), t, mode="a")
            else:
                # existing node
                for nbr in others:
                    if nbr not in self._adjlists[item]:
                        self._adjlists[item] += [nbr]
                        self._update_times((item, nbr), t, mode="a")
                    else:
                        # if node is already in the list we do not add to graph
                        # but we still update the timestamp if it is later
                        if t > self._edgetimes[(item, nbr)]:
                            self._update_times((item, nbr), t, mode="u")

            # update lists of neighboring nodes to include current item
            for nbr in others:
                if nbr not in self._adjlists:
                    if self._log:
                        print "new node added for", nbr
                    self._adjlists[nbr] = [item]
                    self._update_times((nbr, item), t, mode="a")
                elif item not in self._adjlists[nbr]:
                    self._adjlists[nbr] += [item]
                    self._update_times((nbr, item), t, mode="a")
                else:
                    # if item is already in the connecting node's adjacent list
                    # we do not add to graph, but we still update the timestamp
                    # if it is later
                    if t > self._edgetimes[(nbr, item)]:
                        self._update_times((nbr, item), t, mode="u")

    def _purge_old_tweets(self, delta):
        '''Deletes tweets from graph that are older than delta seconds from the
        maximum timestamp.

        Notes:
        a) Log messages are printed to standard output if `self._log` is True
        b) Assumes `self._latesttime` holds the datetime object indicating
        maximum timestamp seen so far.
        c) We delete nodes from adjacency list when they no longer connect to
        other nodes.'''

        for items in self._edgeq:
            # pre: self._edgeq is a list of tuples, sorted in ascending order
            # by the first element which is time (allows us to break early)
            t, keytup = items
            assert self._latesttime >= t

            if (self._latesttime - t).seconds > delta:
                # delete connection from adjacency list
                src, dest = keytup
                oldlist = self._adjlists[src]
                assert dest in oldlist
                if len(oldlist) == 1:  # will be an unconnected node
                    if self._log:
                        print src, "node deleted"
                    del self._adjlists[src]
                else:
                    if self._log:
                        print "delete", dest, "from list of", src
                    self._adjlists[src] = [x for x in oldlist if x != dest]
                # now delete record of timestamp
                self._update_times(keytup, t, mode="d")
            else:
                return  # break early, succeeding elements are later in time

    def _update_times(self, tup, t, mode):
        '''Helper function to updates the time data structures (self._edgetimes
        & self._edqeq).

        Inputs:
            tup: tuple representing an edge (source vertex, destination vertex)
            t: timestamp, datetime object
            mode: "a" to add new edge, "d" to delete, "u" to update timestamp
        '''

        if mode == "a":
            self._edgetimes[tup] = t

            if t >= self._latesttime:
                self._edgeq += [(t, tup)]  # add to end of edgeq
            elif t <= self._edgeq[0][0]:
                self._edgeq = [(t, tup)] + self._edgeq  # add to beginning
            else:
                # insert into right place by time order
                # start from the end (most recent entries) to save time
                for i, item in enumerate(reversed(self._edgeq)):
                    if (i > 0) and (t >= item[0]):
                        self._edgeq[-i:-i] = [(t, tup)]
                        break
            return

        if mode == "u":
            for i, item in enumerate(reversed(self._edgeq)):
                if item[1] == tup:
                    assert self._edgeq[-(i+1)] == item
                    self._edgeq[-(i+1)] = (t, tup)  # update time with new time
                    return

        if mode == "d":
            del self._edgetimes[tup]
            self._edgeq = [x for x in self._edgeq if x[1] != tup]
            return

        # invalid input (should not reach here)
        assert False, "invalid mode"
