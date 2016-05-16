# driver.py

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 2 - Problem 5
#
######################

import sys
import os.path
sys.path.append(os.path.join('..', 'util'))

import set_compiler
set_compiler.install()

import pyximport
pyximport.install()

import numpy as np
from timer import Timer
from animator import Animator
from physics import update, preallocate_locks


def randcolor():
    return np.random.uniform(0.0, 0.89, (3,)) + 0.1

######################
## Subproblem 3:
## added functions to convert integer representations of two
## coordinates to binary and then interleave bitwise
## to obtain a single Morton number in a Morton ordering
## Reference: http://code.activestate.com/recipes/
##            577558-interleave-bits-aka-morton-ize-aka-z-order-curve/

def part1by1(n):
        n&= 0x0000ffff
        n = (n | (n << 8)) & 0x00FF00FF
        n = (n | (n << 4)) & 0x0F0F0F0F
        n = (n | (n << 2)) & 0x33333333
        n = (n | (n << 1)) & 0x55555555
        return n

def interleave2(x, y):
        return part1by1(x) | (part1by1(y) << 1)

######################

if __name__ == '__main__':
    num_balls = 10000
    radius = 0.002
    positions = np.random.uniform(0 + radius, 1 - radius,
                                  (num_balls, 2)).astype(np.float32)

    # make a hole in the center
    while True:
        distance_from_center = np.sqrt(((positions - 0.5) ** 2).sum(axis=1))
        mask = (distance_from_center < 0.25)
        num_close_to_center = mask.sum()
        if num_close_to_center == 0:
            # everything is out of the center
            break
        positions[mask, :] = np.random.uniform(0 + radius, 1 - radius,
                                               (num_close_to_center, 2)).astype(np.float32)

    velocities = np.random.uniform(-0.25, 0.25,
                                   (num_balls, 2)).astype(np.float32)

    # Initialize grid indices:
    #
    # Each square in the grid stores the index of the object in that square, or
    # -1 if no object.  We don't worry about overlapping objects, and just
    # store one of them.
    #
    # Note: we changed the grid_spacing to radius * np.sqrt(2.0) as per 
    # errata published in Piazza post @462
    # was: grid_spacing = radius / np.sqrt(2.0)
    grid_spacing = radius * np.sqrt(2.0)
    grid_size = int((1.0 / grid_spacing) + 1)

    # print grid_size, grid_size * grid_size
    grid = - np.ones((grid_size, grid_size), dtype=np.uint32)

    grid[(positions[:, 0] / grid_spacing).astype(int),
         (positions[:, 1] / grid_spacing).astype(int)] = np.arange(num_balls)

    # A matplotlib-based animator object
    animator = Animator(positions, radius * 2)

    # simulation/animation time variablees
    physics_step = 1.0 / 100  # estimate of real-time performance of simulation
    anim_step = 1.0 / 30  # FPS
    total_time = 0

    frame_count = 0

    ############################
    # added simulation iterations so that it runs for a certain fixed time
    # and ends, giving us a range of min-max-mean simulation frames/s for
    # comparison purposes

    k_iters = 100
    n_iters = k_iters
    min_t = float("inf")
    max_t = 0
    mean_time = 0

    # preallocate locks for objects
    locks_ptr = preallocate_locks(num_balls)

    while True:
        with Timer() as t:
            update(positions, velocities, grid,
                   radius, grid_spacing, locks_ptr,
                   physics_step)

        # udpate our estimate of how fast the simulator runs
        physics_step = 0.9 * physics_step + 0.1 * t.interval
        total_time += t.interval

        frame_count += 1
        if total_time > anim_step:
            animator.update(positions)
            f_t = frame_count / total_time
            print("{} simulation frames per second".format(f_t))

            #########
            #
            # added for performance analysis purposes
            #
            #########
            mean_time = mean_time + f_t
            if f_t<min_t:
                min_t = f_t
            if f_t>max_t:
                max_t = f_t
            n_iters -= 1
            if n_iters==0:
                break
            ##########

            frame_count = 0
            total_time = 0

            # SUBPROBLEM 3: sort objects by location.  Be sure to update the
            # grid if objects' indices change!  Also be sure to sort the
            # velocities with their object positions! 

            # use position of ball on grid, and convert (2-D) grid coordinates
            # to a morton ordering (1-D) for use as a sorting order
            morton = np.empty(num_balls)
            for i in range(num_balls):
                px = (positions[i, 0] / grid_spacing).astype(int)
                py = (positions[i, 1] / grid_spacing).astype(int)
                morton[i] = interleave2(px, py)
            order = np.argsort(morton)

            # apply sort order to positions, velocities
            positions = np.array(positions)[order]
            velocities = np.array(velocities)[order]

            # recalculate grid elements based on new positions
            # if projected position would be slightly off the grid, 
            # assign to nearest grid element
            for i in range(num_balls):

                if positions[i, 0] < radius:
                    px = int(0)
                elif positions[i, 0] > 1.0 - radius:
                    px = (1.0 / grid_spacing).astype(int)
                else:
                    px = (positions[i, 0] / grid_spacing).astype(int)

                if positions[i, 1]<radius:
                    py = int(0)
                elif positions[i, 1] > 1.0 - radius:
                    py = (1.0 / grid_spacing).astype(int)
                else:
                    py = (positions[i, 1] / grid_spacing).astype(int) 

                grid[px, py] = i

    # performance summary
    print("{} iterations in simulation".format(k_iters))
    print("minimum simulation frames per second: {}".format(min_t))
    print("maximum simulation frames per second: {}".format(max_t))
    print("mean simulation frames per second: {}".format(mean_time/k_iters))

