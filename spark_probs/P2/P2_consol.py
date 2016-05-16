# P2_consol.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 2 (all parts)
#
####################

"""This is the script for plotting the Mandelbrot function with 
default partitioning."""

import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.cm as cm

from pyspark import SparkContext
sc = SparkContext()

####################
#
# Instructor-provided functions
#
####################

def mandelbrot(x, y):
    z = c = complex(x, y)
    iteration = 0
    max_iteration = 511  # arbitrary cutoff
    while abs(z) < 2 and iteration < max_iteration:
        z = z * z + c
        iteration += 1
    return iteration

def sum_values_for_partitions(rdd):
    'Returns (as an RDD) the sum of V for each partition of a (K, V) RDD'
    # note that the function passed to mapPartitions should return a sequence,
    # not a value.
    return rdd.mapPartitions(lambda part: [sum(V for K, V in part)])

def draw_image(rdd):
    '''Given a (K, V) RDD with K = (I, J) and V = count,
    display an image of count at each I, J'''

    data = rdd.collect()
    # print data 
    I = np.array([d[0][0] for d in data])
    J = np.array([d[0][1] for d in data])
    C = np.array([d[1] for d in data])
    im = np.zeros((I.max() + 1, J.max() + 1))
    im[I, J] = np.log(C + 1)  # log intensity makes it easier to see levels
    plt.imshow(im, cmap=cm.gray)
    plt.show()


####################
#
# Set-up parameters: canvas size, partitions for vectors of x & y coords
#
####################

N_x = 2000  # number of pixels on x-axis
N_y = 2000  # number of pixels on y-axis

n_x_partitions = 10 
n_y_partitions = 10

####################
#
# Create structures for storing co-ordinates and mandelbrot values
#
####################

x_pixel = sc.parallelize(xrange(N_x), n_x_partitions)
y_pixel = sc.parallelize(xrange(N_y), n_y_partitions)

# create grid of I, J coordinates 
# grid will have (n_x_partitions x n_y_partitions) partitions
grid = x_pixel.cartesian(y_pixel)  

# obtain mandelbrot values at (I, J)
# for draw_image function, we note that (I, J) are pixel co-ordinates
data = grid.map(lambda (i, j): ((i, j), mandelbrot(j/500.0 - 2, i/500.0 - 2)))  

####################
#
# Create outputs: Standard Partitioning
#
####################

# draw mandelbrot plot
draw_image(data)

# get list of values indicating iteration count per partition
work = sum_values_for_partitions(data).collect()

# convert into a numpy array for plt function
hist_values = np.array(work)  

# plot histogram
N_bins = 100
plt.hist(hist_values, bins=N_bins)
plt.title("histogram of iteration count by partition")
plt.xlabel("iteration counts")
plt.ylabel("frequency (by partition)")
plt.savefig("P2a_hist.png", format="png")
plt.show()

####################
#
# Explore partitioning of co-ordinate vectors and grid
# (discussion in P2.txt)
#
# x_pixel.glom().collect()
# grid.glom().collect()
#
####################

####################
#
# Implementing "partition by column"
#
####################

'''
Column-wise partitions: 
for (N_x * N_y) = 4M points, if total number of partitions is to be fixed
at (n_x_partitions x n_y_partitions) = 100, each partition
will hold 40K values; in our example where N_x = 2000, and
we set y to go through all of its 2k values (no partitioning on y), 
we re-order X from (0-1999) into the 100 partitions, 
constituting 20 x-values each but alternating:
(0, 100, 200,... 1900, 1, 101, 201... 1901, [...] 99, 199, 299, ...., 1999)
In other words, each partition will contain every 100th column

Repeating above tasks for new partitioning scheme.
'''

outer_k = n_x_partitions * n_y_partitions  # e.g. 100 partitions
inner_k = N_x / outer_k  # e.g. 20 x-values per partition

newx_range = [outer_k * b + a for a in xrange(outer_k) for b in xrange(inner_k)]

x_pixel2 = sc.parallelize(xrange(N_x), n_x_partitions * n_y_partitions)
y_pixel2 = sc.parallelize(xrange(N_y), 1)  # take whole column
grid2 = x_pixel2.cartesian(y_pixel2)  

data2 = grid2.map(lambda (i, j): ((i, j), mandelbrot(j/500.0 - 2, i/500.0 - 2)))
draw_image(data2) 

# plot histogram
work2 = sum_values_for_partitions(data2).collect()
hist_values = np.array(work2)  # convert into a numpy array for plt function
plt.hist(hist_values/10e7, bins=N_bins)
plt.title("histogram of iteration count by partition (column strategy)")
plt.xlabel("iteration counts x 10e7")
plt.ylabel("frequency (by partition)")
plt.xlim(0,0.1)
plt.savefig("P2c_hist.png", format="png")
plt.show()

####################
#
# Implementing "using built-in repartition"
#
####################

'''Repartioning original grid using pyspark's built-in repartitioning function.'''

grid3 = grid.repartition(100)  
data3 = grid3.map(lambda (i, j): ((i, j), mandelbrot(j/500.0 - 2, i/500.0 - 2)))
draw_image(data3)

# plot histogram
work3 = sum_values_for_partitions(data3).collect()
hist_values = np.array(work3)  # convert into a numpy array for plt function
plt.hist(hist_values/10e7, bins=N_bins)
plt.title("histogram of iteration count by partition (repartition function)")
plt.xlabel("iteration counts x 10e7")
plt.ylabel("frequency (by partition)")
plt.xlim(0,0.1)
plt.savefig("P2b_hist.png", format="png")
plt.show()

####################
#
# Implementing "randomize grid elements (non-Spark pre-processing)"
#
####################

'''Shuffle elements in grid using `random` package'''

import random
random.seed(123)

# could make randomized chunks and save-as-you-go in rdds if local memory 
# is an issue; here we generate list of all tuples in python
grid4 = [(i, j) for i in xrange(N_x) for j in xrange(N_y)]
random.shuffle(grid4)

# create rdd using randomized co-ordinates
grid4_rdd = sc.parallelize(grid4, n_x_partitions * n_y_partitions)

data4 = grid4_rdd.map(lambda (i, j): ((i, j), mandelbrot(j/500.0 - 2, i/500.0 - 2)))
draw_image(data4)

# plot histogram
work4 = sum_values_for_partitions(data4).collect()
hist_values = np.array(work4)  # convert into a numpy array for plt function
plt.hist(hist_values/10e7, bins=N_bins)
plt.title("histogram of iteration count by partition (python randomization)")
plt.xlabel("iteration counts x 10e7")
plt.ylabel("frequency (by partition)")
plt.xlim(0.018,0.022)
plt.savefig("P2d_hist.png", format="png")
plt.show()