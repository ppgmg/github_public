# cluster.py

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 181 - Spring 2016
#
# Homework 4: Clustering - Problem 3
#
# Email: klo@g.harvard.edu
#
######################

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


class KMeans(object):
    # K is the K in KMeans
    # useKMeansPP is a boolean. If True, you should initialize using KMeans++
    def __init__(self, K, useKMeansPP):
        self.K = K
        self.useKMeansPP = useKMeansPP

    # X is a (N x 28 x 28) array where 28x28 is the dimensions of each of
    # the N images.
    def fit(self, X):

        def dist_to_mean(x, y):
            # calculate square of L2 distance between two vectors
            return np.sum((x - y)**2)

        # Reference: "Lloyd's Algorithm", March 10/16 lecture notes
        # extract dimensions
        self.N = X.shape[0]  # (e.g. 6000)
        self.i = X.shape[1]  # (e.g. 28)
        self.j = X.shape[2]  # (e.g. 28)

        # let's work with one long vector of values rather than 2x2 grid
        # facilitate use of dot product later
        # http://stackoverflow.com/questions/13990465/3d-numpy-array-to-2d
        self.npixels = self.i * self.j
        X_as_2D = X.copy()
        X_as_2D = X_as_2D.reshape((self.N, self.npixels))

        # z is a matrix that uses one-hot encoding to identify the
        # cluster k to which an image belongs; distances is the corresponding
        # distance to the mean of that cluster
        z = np.zeros((self.N, self.K))
        distances = np.zeros(self.N)
        clust_means = np.zeros((self.K, self.npixels))

        J = []  # value of objective function

        # initializations
        if self.useKMeansPP:
            # implement K-means++
            # reference: https://en.wikipedia.org/wiki/K-means%2B%2B
            inits = np.zeros(self.K)  # indices of initial centers
            # 1. randomly choose an image as center
            inits[0] = np.random.randint(0, self.N)
            # 2. for each data point, compute the distance to nearest center
            for i in range(1, self.K):
                tempdist = np.zeros(self.N)
                for j in range(i):  # compare only to existing centers
                    # print "i: %i, j: %i, initsj: %i" % (i, j, inits[j])
                    if j == 0:
                        tempdist = np.array([dist_to_mean(X_as_2D[row],
                                    X_as_2D[inits[0]])
                                    for row in range(self.N)])
                    else:
                        tempdist = np.array([np.minimum(tempdist[row],
                                    dist_to_mean(X_as_2D[row],
                                    X_as_2D[inits[j]]))
                                    for row in range(self.N)])
                # Choose one new data point at random as a new center, using a
                # weighted probability distribution where a point x is chosen
                # with probability proportional to D(x)^2 (tempdist is squared).
                tempdist = tempdist * 1.0 / np.sum(tempdist)  # normalize
                inits[i] = np.random.choice(np.arange(self.N), p=tempdist)

            inits = inits.astype(int)
            self.plot_starting_images(inits)

            # assign cluster for each point based on distance to means
            for row in xrange(self.N):
                min_distance = np.inf  # initialize
                c = -1
                for clindex in xrange(self.K):
                    temp = dist_to_mean(X_as_2D[row], X_as_2D[inits[clindex]])
                    if temp < min_distance:
                        min_distance = temp  # set minimum distance
                        c = clindex  # set cluster
                z[row, c] = 1
        else:
            # randomly assign each image to one of K clusters
            rand_clust = np.random.randint(0, self.K, self.N)
            for i in xrange(self.N):
                z[i, rand_clust[i]] = 1

        # stopping and convergence criteria
        max_iters = 1000
        converged = False

        # initialization
        old_z = z.copy()  # keep track of previous z to check if changed

        for i in xrange(max_iters):
            # compute cluster means (i.e. k x (i x j) array of mean values)
            # 1. collect sum of (i x j) values, by cluster
            pts_by_k = np.dot(z.T, X_as_2D)  # (k x n)(n x (i x j)) -> k x (i x j)
            # 2. divide by number of (i x j) arrays that were added to get mean
            pts_per_k = np.sum(z, axis=0)  # by column -> length k
            # 3. element-wise division (i.e. each (i x j) by pts_per_k entry)
            # http://stackoverflow.com/questions/19602187/numpy-divide-each-row-by-a-vector-element
            clust_means = pts_by_k * 1.0 / pts_per_k[:, None]  # k x (i x j)

            # recalculate assigned cluster for each point
            # distance to nearest mean
            z = np.zeros((self.N, self.K))  # re-initialize
            for row in xrange(self.N):
                min_distance = np.inf  # initialize
                c = -1
                for clindex in xrange(self.K):
                    temp = dist_to_mean(X_as_2D[row], clust_means[clindex])
                    if temp < min_distance:
                        min_distance = temp  # set minimum distance
                        c = clindex  # set cluster
                z[row, c] = 1
                distances[row] = min_distance

            # stopping criteria
            if np.array_equal(z, old_z):
                converged = True
                print "converged after %i iterations" % i
                break
            # else
            print "total of distances to cluster means ", np.sum(distances)
            J.append(np.sum(distances))
            old_z = z
            # end loop

        assert converged, "did not converge"

        # reporting
        self.finalz = z
        self.finald = distances
        self.finalcmeans = clust_means
        print "distribution (images per cluster) ", sorted(np.sum(self.finalz,
                                                           axis=0).astype(int))
        self.get_mean_images()
        self.get_representative_images()
        self.plot_objective_function(J)
        return

    def plot_objective_function(self, J):
        # J is a vector of values
        plt.plot(np.arange(len(J)), J)
        plt.title("objective function")
        plt.xlabel("iteration")
        plt.show()

    def plot_starting_images(self, indexes):
        plt.figure()
        cols = 3
        if self.K % 3 == 0:
            rows = self.K / 3
        else:
            rows = self.K / 3 + 1

        for k in range(self.K):
            plt.subplot(rows, cols, k+1)
            plt.imshow(pics[indexes[k]], cmap='Greys_r')

        plt.suptitle("initial cluster means")
        plt.show()

    # This should return the arrays for K images. Each image should represent the mean of each of the fitted clusters.
    def get_mean_images(self):
        # note that the "mean" image does not have to be an actual image
        if self.K <= 3:
            # if 3 or fewer classes, we will display image one at a time
            for k in range(self.K):
                KMeansClassifier.create_image_from_array(self.finalcmeans[k].
                                                    reshape((self.i, self.j)))
        else:
            # custom n x 3 grid
            plt.figure()
            cols = 3
            if self.K % 3 == 0:
                rows = self.K / 3
            else:
                rows = self.K / 3 + 1

            for k in range(self.K):
                plt.subplot(rows, cols, k+1)
                plt.imshow(self.finalcmeans[k].reshape((self.i, self.j)),
				           cmap='Greys_r')

            plt.suptitle("mean images by cluster")
            plt.show()

    # This should return the arrays for D images from each cluster that are representative of the clusters.
    def get_representative_images(self, D=9):
        # our strategy to show D representative images is to use the distances
        # of each image from its respective cluster mean, and take a sample,
        # at roughly equal intervals, of images from each cluster;
        # that is from the nearest image to the mean, to the furthest.
        # In this way, we can visualize the range of images for each cluster
        for k in range(self.K):
            col = self.finalz[:, k]
            count = np.sum(col)
            # we use the inverse of distance so that we can take maximum
            # and leave 0-value elements that are not part of the cluster
            invdist = np.multiply(1.0/self.finald, col)  # element-wise multiply
            # http://stackoverflow.com/questions/6910641/how-to-get-indices-of-
            # n-maximum-values-in-a-numpy-array
            # sorted indices (closest to furthest):
            idxlist = np.argsort(invdist)[-count:][::-1]
            assert len(idxlist) == count

            if D < count:
                # pick subset of images to show
                select = np.linspace(0, count-1, D).astype(int)
                idxlist = idxlist[select]
                assert len(idxlist) == D

            if D != 9:
                # if custom value assigned, we will display image one at a time
                for idx in idxlist:
                    KMeansClassifier.create_image_from_array(pics[idx])
            else:
                # custom 3 x 3 grid
                plt.figure()
                for i, idx in enumerate(idxlist):
                    plt.subplot(3, 3, i+1)
                    plt.imshow(pics[idx], cmap='Greys_r')
                plt.suptitle("representative images, cluster " + str(k))
                plt.show()

        return

    # img_array should be a 2D (square) numpy array.
    # Note, you are welcome to change this function (including its arguments and return values) to suit your needs.
    # However, we do ask that any images in your writeup be grayscale images, just as in this example.
    def create_image_from_array(self, img_array):
        plt.figure()
        plt.imshow(img_array, cmap='Greys_r')
        plt.show()
        return

# This line loads the images for you. Don't change it!
pics = np.load("images.npy", allow_pickle=False)

# You are welcome to change anything below this line. This is just an example of how your code may look.
# That being said, keep in mind that you should not change the constructor for the KMeans class,
# though you may add more public methods for things like the visualization if you want.
# Also, you must cluster all of the images in the provided dataset, so your code should be fast enough to do that.
K = 10
KMeansClassifier = KMeans(K, useKMeansPP=True)
KMeansClassifier.fit(pics)
