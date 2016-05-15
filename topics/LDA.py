# CS 181, Spring 2016
# Homework 5: EM
# Name: Kendrick Lo (ID: 70984997)
# Email: klo@g.harvard.edu

# process book can be found at testing.ipynb (IPython Notebook)

import numpy as np
import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
# import scipy as sc
from scipy import misc
import sys


class LDA(object):

    # Initializes with the number of topics
    def __init__(self, num_topics):
        self.num_topics = num_topics

    def neg_log_like(self, currg, currw, currbeta, currtheta):
        '''
        Our objective function to minimize.
        To sum over all indices in a triple sum of a product, we calculate the
        dot product of the matrix elements and then sum only the diagonal
        elements: https://en.wikipedia.org/wiki/Trace_(linear_algebra)
        Note: gamma is D x K, w is D x V, beta_k is K x V, theta is K x 1
        '''

        term1 = np.sum(np.diagonal(np.dot(currg.T, np.dot(currw, np.log(currbeta + 1e-100).T))))
        term2 = np.sum(np.dot(currg, np.log(currtheta + 1e-100)))

        return -1.0 * (term1 + term2)

    # This should run the M step of the EM algorithm
    def M_step(self, gamma, w):
        # M Step
        # Get new values for theta and beta_k
        # Recall:
        #   theta: proportion of topic k across all documents (vector, length K)
        #   beta_k: for the kth topic, beta_k is the probability of seeing the
        #     v'th word across all V possible words in the vocabulary (array, K x V)
        theta = np.mean(gamma, axis=0)  # mean over columns

        temp = np.dot(gamma.T, w)
        row_sums = temp.sum(axis=1, keepdims=True)
        beta_k = temp * 1.0 / row_sums  # normalized dot product

        return theta, beta_k

    # This should run the E step of the EM algorithm
    def E_step(self, w, beta_k, theta):
        # E Step
        # Evaluate posterior distribution for Z
        # gamma is a D x K matrix: probabilities that words of document d
        # belongs to topic k
        # Note: theta is a constant, distribution applies to each document

        prod = (np.dot(w, np.log(beta_k + 1e-100).T) +
                np.tile(np.log(theta + 1e-100), (D, 1)))

        # normalize the rows, convert into probabilities
        logsums = np.apply_along_axis(misc.logsumexp, 1, prod)  # by row
        # subtract log for row, and re-exponentiate
        result = np.exp(prod - logsums[:, np.newaxis])
        # assert np.isclose(np.sum(result), D)  # D rows add up to 1
        return result  # gamma

    # This should print the topics that you find
    def print_topics(self):

        #####
        # initialize parameters
        #####

        K = self.num_topics
        # theta: proportion of topic k across all documents (vector, length K)
        theta = np.random.dirichlet(np.ones(K))
        # beta_k: for the kth topic, beta_k is the probability of seeing the
        # vth word across all V possible words in the vocabulary (array, K x V)
        beta_k = np.random.dirichlet(np.ones(V), size=K)

        max_iters = 100  # maximum iterations
        # beta_trace = [beta_k]  # uncomment if trace is desired
        obj_function = []  # trace

        #####
        # main loop
        #####

        for i in xrange(max_iters):

            print "beginning iteration", i; sys.stdout.flush()

            # E step
            w = counts
            gamma = self.E_step(w, beta_k, theta)

            # M step
            old_beta_k = beta_k  # remember old beta
            theta, beta_k = self.M_step(gamma, w)

            # Stopping Criterion
            # Since we are most interested in beta_k, we see if beta_k stops changing
            # if so, we terminate; otherwise, loop

            # beta_trace.append(beta_k)  # uncommon if trace is desired
            Q = self.neg_log_like(gamma, w, beta_k, theta)
            obj_function.append(Q)  # negative log likelihood

            if np.allclose(old_beta_k, beta_k, atol=1e-5):
                print "convergence"
                break
            else:
                print Q
        # endloop

        # plt.figure()
        # plt.plot(obj_function)
        # plt.show()

        #####
        # print topics
        #####

        wpt = 15  # number of words per topic to print

        print "Number of Topics:", self.num_topics
        print "---------------------"

        for k in xrange(K):
            print "top words for topic", k
            # reverse sort, get actually id and print word
            print [word[word_ids[idx]] for idx in np.argsort(beta_k[k])[::-1][:wpt]]

        return

#######################################################################
# This line loads the text for you. Don't change it!
text_data = np.load("text.npy", allow_pickle=False)
with open('words.txt', 'r') as f:
    word_dict_lines = f.readlines()

# setup

doc_ids = list(set([int(item) for item in text_data[:, 0]]))
word_ids = list(set([int(item) for item in text_data[:, 1]]))

#####
# populate weight array
#####

# we assume if there happens to be two counts for the same (doc, word)
# we choose the one later in the list to store
# (overwrites earlier values)
L = text_data.shape[0]
D = len(doc_ids)
V = len(word_ids)
# construct D x V array of counts (# make 0-indexed)
counts = np.zeros((D, V))

for row in xrange(L):
    if row % 10000 == 0:
        print "completed %i iterations of %i" % (row, L)
    counts[int(text_data[row][0]) - 1,
           word_ids.index(int(text_data[row][1]))] = int(text_data[row][2])

#####
# populate word id dictionary
#####

word = {}

for line in word_dict_lines:
    id_word = line.split()
    word[int(id_word[0])] = id_word[1]

testing_set = [15]  # [5, 10, 15]
for set_k in testing_set:
    LDAClassifier = LDA(num_topics=set_k)
    LDAClassifier.print_topics()
