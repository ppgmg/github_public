# P2b.py

####################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 1 - Problem 2 Part b
#
####################

"""This is the script for plotting the Mandelbrot function using pyspark's 
built-in repartitioning function."""

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

####################
#
# Implementing "using built-in repartition"
#
####################

'''Repartioning original grid using pyspark's built-in repartitioning function.'''

grid3 = grid.repartition(100)

# obtain mandelbrot values at (I, J)
# for draw_image function, we note that (I, J) are pixel co-ordinates  
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