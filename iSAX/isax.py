import numpy as np
from scipy import stats

####################
#
# HELPER FUNCTIONS
#
####################


def stand(x):
    '''
    Standardizes a time series

    Parameters
    ----------
    x : 1-d numpy array
        Time series to be standardized

    Returns
    -------
    1-d numpy array with standardized time series values
    '''

    return (x - np.mean(x)) / np.std(x, ddof=0)


def get_breakpoints(a):
    '''
    Return list of breakpoints given cardinality a, used in SAX indexing.

    Parameters
    ----------
    a : integer
        Number of breakpoints

    Returns
    -------
    List of floats representing standard deviations from 0 mean, length (a - 1)
    '''

    avec = np.zeros(a - 1)  # 1 less breakpoint than length
    for i in range(a - 1):
        avec[i] = stats.norm.ppf((i + 1) / a, loc=0, scale=1)
    return avec


def get_isax_word(ts, w, a):
    '''
    Given a time series, return iSAX word representation.

    Parameters
    ----------
    ts: 1d numpy array
        Time series values
    w : int
        Number of chunks in which to divide time series
    a: int
        Cardinality (number of possible index values/levels per chunk)

    Notes:
    Unexpected results may occur if cardinality is not 2^n for some n.
    Rounding errors may occur if w does not divide into length of time series
    evenly.

    Returns
    -------
    List of strings of length w, where each string represents a binary number
    with log2(a) digits
    '''

    # standardize time series
    series = stand(ts)

    # divide series into chunks
    if len(series) >= w:
        lenchunk = int(len(series) / w)
    else:
        # we choose to divide into unit chunks if the length of series
        # is not at least w
        lenchunk = 1

    # get averages of each bin
    means = [np.mean(series[int(lenchunk * chunk):int(lenchunk * (chunk + 1))])
             for chunk in range(w)]

    breakpoints = get_breakpoints(a)

    if len(breakpoints) != (a - 1):
        return ValueError('Not compatible with tree structure.')

    # reverse list so that 0 value is lowest y (most negative on std scale)
    labels = np.arange(a)[::-1]
    if len(labels) != a:
        return ValueError('Not compatible with tree structure.')

    # convert to SAX code
    sax = np.empty(w, dtype=int)
    for i, item in enumerate(means):
        for j, b in enumerate(breakpoints):
            if item < b:
                sax[i] = int(labels[j])
                break
            elif j == len(breakpoints)-1:
                # that was the last breakpoint, value must be greater
                sax[i] = int(labels[j+1])

    # convert to binary format
    digits = int(np.log2(len(labels)))
    binarysax = [format(item, '0' + str(digits) + 'b') for item in sax]

    return binarysax


def distance(ts1, ts2):
    '''
    Calculates Euclidian distance between two time series. Assumes time series
    are of the same length.

    Used by `find_nbr` in `iSaxTree` class to compare time series. Other
    distance measures can be substituted here.

    Parameters
    ----------
    ts1 : 1d numpy array
        Time series values
    ts2 : 1d numpy array
        Time series values

    Returns
    -------
    Float, distance between the two time series.
    '''

    if len(ts1) != len(ts2):
        return ValueError('Not compatible with tree structure.')

    d = (ts1 - ts2)**2
    d = d.sum(axis=-1)
    d = np.sqrt(d)

    return d

####################
#
# FILE SYSTEM FUNCTIONS
#
# currently iSAX word (string) is used as the filename;
# these functions store the "files" in memory
#
# Note that the storage structure (alldata) works differently from the
# `keyhashes` dictionary for the iSaxTree classes; the former only has an
# iSAX word index if there are existing time series being stored for it
# (e.g. upon deletion of all time series for that word, the entry from
# `alldata` is deleted.  However, in the `keyhashes` dictionary, iSAX words
# are stored for internal nodes (to which data items are not associated) and
# occasionally, for leaf nodes where all the corresponding time series have
# been deleted (i.e. nodes in the iSaxTree are NOT deleted even when they
# are empty.)
#
####################


class TreeFileStructure:

    def __init__(self):
        '''
        Initializes the TreeFileStructure class.

        Parameters
        ----------
        None

        Returns
        -------
        An initialized TreeFileStructure object.
        '''

        # can be re-initialized if desired
        self.alldata = {}

    def read_file(self, filename):
        '''
        Returns a list of time series associated with an iSAX word

        Parameters
        ----------
        filename : string
            iSAX word

        Returns
        -------
        A list of tuples:
        [(time series as numpy array, time series ID), ...]
        '''
        templist = []
        try:
            templist = self.alldata[filename]
        except:
            pass
        return templist

    def isax_exists(self, filename):
        '''
        Checks whether an iSAX word has any time series associated
        with it.

        Parameters
        ----------
        filename : string
            iSAX word

        Returns
        -------
        Boolean, whether there are any time series stored with the iSAX word
        '''
        return filename in self.alldata

    def already_in_file(self, filename, ts):
        '''
        Checks whether a specific time series is stored with an iSAX word

        Parameters
        ----------
        filename : string
            iSAX word
        ts : 1d numpy array
            Time series values

        Returns
        -------
        Boolean, whether a specific time series is stored with an iSAX word.
        '''
        if self.isax_exists(filename):
            # read data
            data = self.read_file(filename)
            exists = np.any([np.array_equal(item[0], ts) for item in data])
            if exists:
                return True

        # not in file
        return False

    def write_to_file(self, filename, ts, tsid=''):
        '''
        Adds a time series to the iSAX file system.

        Parameters
        ----------
        filename : string
            iSAX word
        ts : 1d numpy array
            Time series values
        tsid : string
            Time series identifier (equivalent to DictDB primary key)

        Returns
        -------
        Nothing, modifies in-place.
        '''

        # assumes already checked not in file
        # write time series to `filename` with optional ID
        if self.isax_exists(filename):
            self.alldata[filename] += [(ts, tsid)]
        else:
            # write new file / entry
            self.alldata[filename] = [(ts, tsid)]

    def delete_from_file(self, filename, ts):
        '''
        Removes a time series from the iSAX file system.

        Parameters
        ----------
        filename : string
            iSAX word
        ts : 1d numpy array
            Time series values
        tsip : string
            Time series identifier (equivalent to DictDB primary key)

        Returns
        -------
        Nothing, modifies in-place.
        '''
        # deletes time series from storage
        self.alldata[filename] = [item for item in self.alldata[filename]
                                  if not np.array_equal(item[0], ts)]
        # delete if empty
        if len(self.alldata[filename]) == 0:
            del self.alldata[filename]


####################
#
# TREE STRUCTURES
#
####################

class log:
    '''
    String representation of iSAX tree.
    '''

    def __init__(self):
        '''
        Initializes the log class. Used to store string representation
        of iSAX tree through recursive function.

        Parameters
        ----------
        None

        Returns
        -------
        An initialized log object.
        '''
        self.graphstr = ''

    def graph_as_string(self):
        '''
        Returns the string representation of the iSAX tree.
        Note: should have been previously calculated.

        Parameters
        ----------
        None

        Returns
        -------
        An initialized log object.
        '''
        return self.graphstr


class BasicTree:
    '''
    Basic n-ary tree class.
    '''

    def __init__(self, data, parent=None):
        '''
        Initializes the BasicTree class, i.e. basic n-ary tree.

        Parameters
        ----------
        data : str
            String representation of the node
        parent : tree node
            The parent node to the node being initialized

        Returns
        -------
        An initialized BasicTree object.
        '''
        self.data = data
        self.parent = parent
        # stores pointers to child nodes
        self.child_pointers = []

    def add_child(self, data, level):
        '''
        Adds a child to the tree.

        Parameters
        ----------
        data : str
            String representation of child node name
        level : tree node
            Current tree level, i.e. will be the parent of the child node

        Returns
        -------
        An initialized Basic Tree object that represents the new child node.
        '''
        n = self.__class__(data, self, level)
        self.child_pointers += [n]
        return n

    def num_children(self):
        '''
        Calculates the number of children nodes.

        Parameters
        ----------
        None

        Returns
        -------
        The number of children nodes.
        '''
        return len(self.child_pointers)

    def isRoot(self):
        '''
        Determines whether the current node is the root of the overall tree.

        Parameters
        ----------
        None

        Returns
        -------
        Whether the current node is the root, i.e. it does not have a
        parent node.
        '''
        return not self.parent


class iSaxTree(BasicTree):
    '''
    Implements modified version of iSAX tree.

    See: http://www.cs.ucr.edu/%7Eeamonn/iSAX_2.0.pdf for reference.
    In original form, during construction of iSAX indexing tree, multiple iSAX
    words have the root as parent, whereas internal nodes are limited to at
    most two children (see II. C.), and additionally, a node splitting policy
    is used to increase the likelihood that a given leaf being converted into
    an internal node will have its data more evenly distributed resulting in
    a more balanced tree.

    However, that implementation does not guarantee better balance,
    particularly if two series are very close in value throughout. Furthermore,
    the requirement that internal nodes be roots of binary subtrees appears to
    be needlessly restrictive.

    Accordingly, we adapt the n-ary nature of the top level of the iSAX tree
    for use at each level; when a leaf node is to be converted into an internal
    node, the data to be re-stored in a child node can take on any iSAX word
    value of the higher cardinality (i.e. we can have more than 2 leaves per
    internal node, are are not limited to binary splits.) This is just as
    likely (if not more likely) to keep the tree balanced, while controlling
    the height of the tree. As new leaves do not result in the creation of a
    new file when empty, no additional file space is required to implement the
    n-ary subtrees.

    Notes:

    1. Currently only permits one instance of a time series to be stored
    (should be rare if values are floats). Duplicate time series are ignored,
    even if they have different labels.

    2. Deleting a time series from tree requires series to be provided as
    input; i.e. time series <-> series ID conversion not provided by this
    class.

    3. Assumes `alldata` is an accessible dictionary that stores time series
    data, with iSAX word as key, and value is a list of tuples [(time series as
    a numpy array, time series ID), ...]  Currently, ISAX-indexed time series
    data is stored in memory; modifications are required to implement writes
    to persistent storage.
    '''

    def __init__(self, data, parent=None, level=0):
        '''
        Initializes tree (or subtree).
        Note: leave level unspecified to create the root node of a new tree.

        Parameters
        ----------
        data : str
            String representation of the node
        parent : tree node
            The parent node to the node being initialized
        level : int
            The current level in the tree (0 = root)

        Returns
        -------
        An initialized iSaxTree class.
        '''

        super().__init__(data, parent)

        # dictionary with isax words associated with this level as keys
        # and list of child_pointers as value
        self.keyhashes = {}

        # current level
        self.level = level

        # adjustable parameters

        # number of chunks
        self.w = 4

        # base cardinality
        self.a = 4

        # threshold number of series per file
        # (can be increased for larger datasets)
        self.TH = 5

        # maximum depth (number of levels) in tree to split
        self.maxlevel = 10

    def insert(self, ts, fs, level=1, tsid=''):
        '''
        Attempts insertion at a given level of the tree (default is below root)

        Notes:
        1. Format of time series should be a 1-D numpy array
        (e.g. array([ 26.2,  25.9 ,  25.71,  25.84,  25.98,  25.73, ...)
        may not work correctly if time series of different lengths are inserted
        2. Series ID (string) is optional, but must be specified with `tsid`
        if used
        3. Currently, threshold for maximum number of series per file is
        applied up to `maxlevel` to control height of tree; at `maxlevel`
        series is added to a child node even if threshold number of series
        is exceeded

        Parameters
        ----------
        ts : 1d numpy array
            Time series values
        fs : TreeFileStructure
            The iSAX tree "file structure" that collects the time series data
        level : int
            The level of the tree (0 = root)
        tsid : str
            Unique time series identifier, equivalent to database
            primary key

        Returns
        -------
        Nothing, modifies in-place.
        '''

        # level to add node must be one below current node's level
        if level != (self.level + 1):
            return ValueError('Not compatible with tree structure.')

        # get iSAX representation of input time series (as string)
        isax_word = str(get_isax_word(ts, self.w, self.a*(2**(level-1))))

        if fs.already_in_file(isax_word, ts):
            # exact match already in file
            return

        if isax_word in self.keyhashes:
            # a node for the same iSAX word has previously been created;
            # can be leaf or an internal node
            # identify the pointer that points to the correct child
            idx = self.keyhashes[isax_word]
            node = self.child_pointers[idx]

            if node.num_children() == 0:
                # child is a terminal node / leaf
                if node.data != isax_word:
                    return ValueError('Not compatible with tree structure.')
                # there is space to add series to the leaf
                if len(fs.read_file(isax_word)) < self.TH:
                    fs.write_to_file(isax_word, ts, tsid=tsid)
                # add to leaf if maximum depth reached
                # (i.e. do not split further)
                elif level == self.maxlevel:
                    fs.write_to_file(isax_word, ts, tsid=tsid)
                # additional insert warrants a split, create an internal node
                else:

                    # get all time series associated with this node and
                    # reinsert into new subtree
                    ts_list = fs.alldata[isax_word]
                    for ts_to_move, itemid in ts_list:
                        node.insert(ts_to_move, fs, level + 1, tsid=itemid)
                        fs.delete_from_file(str(get_isax_word(
                            ts_to_move, self.w, self.a * (2 ** (level - 1)))),
                            ts_to_move)

                    # insert input time series that triggered split
                    # into a node in the new subtree (i.e. one level down)
                    node.insert(ts, fs, level + 1, tsid=tsid)
            else:
                # child is an internal node (i.e. not a terminal node);
                # traverse to next level
                node.insert(ts, fs, level + 1, tsid=tsid)
        else:
            # new node to be created; add pointer to new terminal node
            # in self's list
            self.keyhashes[isax_word] = self.num_children()  # 0-index
            fs.write_to_file(isax_word, ts, tsid=tsid)
            self.add_child(isax_word, level)

        return

    def delete(self, ts, fs, level=1):
        '''
        Deletes a time series from the tree.

        Parameters
        ----------
        ts : 1d numpy array
            Time series values
        fs : TreeFileStructure
            The iSAX tree "file structure" that collects the time series data
        level : int
            The level of the tree (0 = root)

        Returns
        -------
        Nothing, modifies in-place.
        '''

        # get iSAX representation of input time series (as string)
        isax_word = str(get_isax_word(ts, self.w, self.a * (2 ** (level - 1))))

        if fs.already_in_file(isax_word, ts):
            # exact match already in file
            fs.delete_from_file(isax_word, ts)
            return

        # a node for the same iSAX word has previously been created;
        # can be leaf or an internal node
        if isax_word in self.keyhashes:
            # identify the pointer that points to the correct child
            idx = self.keyhashes[isax_word]
            node = self.child_pointers[idx]

            if node.num_children() == 0:  # child is a terminal node
                if node.data != isax_word:
                    return ValueError('Not compatible with tree structure.')
                # if code reaches here, word is not in node otherwise it would
                # have already been deleted since it should be stored filed
                # under `isax_word`
            else:
                # child is an internal (i.e. not a terminal node); traverse
                node.delete(ts, fs, level + 1)
        else:
            pass
            # there was no node created for this isax_word;
            # therefore it cannot be in tree
        return

    def preorder_str(self, l, fs):
        '''
        Recursively creates string representation of iSAX tree.

        Parameters
        ----------
        l : log
            Log object, used to store string representation through recursion
        fs : TreeFileStructure
            The iSAX tree "file structure" that collects the time series data

        Returns
        -------
        String representation of iSAX tree.
        '''

        if self.isRoot():
            paddedstr = self.data + '\n'
            l.graphstr += paddedstr
        else:
            if fs.isax_exists(self.data):
                count = len(fs.read_file(self.data))
                listing = [item[1] for item in fs.read_file(self.data)]
            else:
                count = 0
                listing = []
            paddedstr = ('---' * self.level + '>' + self.data + ': ' +
                         str(count) + ' ' + str(sorted(listing)) + '\n')
            l.graphstr += paddedstr

        # recursively traverse tree
        for child_link in self.child_pointers:
            child_link.preorder_str(l, fs)

    def find_nbr(self, ts, fs, level=1):
        '''
        Performs an approximate search for the nearest neighbor of the
        input time series

        Notes:

        1. Nearest neighbor is 'approximate' since we are taking advantage of
        the format of the natural clustering provided by the iSAX tree to
        determine potential close matches. The intuition is that two similar
        time series are often represented by the same iSAX word. Another
        algorithm that potentially performs an exhaustive search should be
        used if an exact search is required.
        2. In the event that no neighbors with the same iSAX word can be found,
        neighboring series that share the same parent iSAX word (but not the
        root) are considered to find the nearest neighbor. Otherwise, a null
        suggestion is returned.
        3. The input/reference time series should be a 1-D numpy array; the
        input time series need not be an existing time series in tree.

        Parameters
        ----------
        ts : 1d numpy array
            Time series values
        fs : TreeFileStructure
            The iSAX tree "file structure" that collects the time series data
        level : int
            The level of the tree (0 = root)

        Returns
        -------
        The primary key of the closest time series and its distance from the
        query time series. Returns None if no neighbor is found.
        '''

        # get iSAX representation of input time series (as string)
        isax_word = str(get_isax_word(ts, self.w, self.a * (2 ** (level - 1))))

        # exact isax word match found in file, retrieve all series
        if fs.isax_exists(isax_word):
            ts_list = fs.read_file(isax_word)
            if len(ts_list) == 0:
                return ValueError('Not compatible with tree structure.')

            # one entry, return it
            if len(ts_list) == 1:
                return {ts_list[0][1]: 0}

            # calculate distances from reference series to each located
            # series and return closest
            else:
                mindist = np.inf
                best_id = ""
                for item in ts_list:
                    tempdist = distance(ts, item[0])
                    if tempdist < mindist:
                        mindist = tempdist
                        best_id = item[1]
                return {best_id: mindist}

        # if isax_word is in keyhashes dictionary, but not in file system
        # then this means we need to check the children for potential matches
        if isax_word in self.keyhashes:
            # identify the pointer that points to the correct child
            idx = self.keyhashes[isax_word]
            node = self.child_pointers[idx]

            # child is a terminal node
            if node.num_children() == 0:
                if node.data != isax_word:
                    return ValueError('Not compatible with tree structure.')
                # if code reaches here, node was created but it is empty
                # create list of neighboring series from nodes that have
                # shared parent
                ts_list = []
                for child in self.child_pointers:
                    try:
                        ts_list += fs.read_file(child.data)
                    except:
                        # node may exist, but no series are stored in the
                        # file system
                        pass

                if len(ts_list) > 0:
                    # calculate distances to each time series; return minimum
                    mindist = np.inf
                    best_id = ""
                    for item in ts_list:
                        tempdist = distance(ts, item[0])
                        if tempdist < mindist:
                            mindist = tempdist
                            best_id = item[1]
                    return {best_id: mindist}
                # no neighbors found at the same level
                else:
                    return None
            else:
                # child is an internal (i.e. not a terminal node); traverse
                return node.find_nbr(ts, fs, level + 1)
            # there was no node created for this isax_word
        else:
            pass
