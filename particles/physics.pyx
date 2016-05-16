#cython: boundscheck=False, wraparound=False

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# CS 205 - Computing Foundations for Computational Science (Prof. R. Jones)
# 
# Homework 2 - Problem 5
#
######################

cimport numpy as np
from libc.math cimport sqrt
from libc.stdint cimport uintptr_t
cimport cython
from omp_defs cimport omp_lock_t, get_N_locks, free_N_locks, acquire, release
from cython.parallel import prange

# Useful types
ctypedef np.float32_t FLOAT
ctypedef np.uint32_t UINT

cdef inline int overlapping(FLOAT *x1,
                            FLOAT *x2,
                            float R) nogil:
    cdef:
        float dx = x1[0] - x2[0]
        float dy = x1[1] - x2[1]
    return (dx * dx + dy * dy) < (4 * R * R)


cdef inline int moving_apart(FLOAT *x1, FLOAT *v1,
                             FLOAT *x2, FLOAT *v2) nogil:
    cdef:
        float deltax = x2[0] - x1[0]
        float deltay = x2[1] - x1[1]
        float vrelx = v2[0] - v1[0]
        float vrely = v2[1] - v1[1]
    # check if delta and velocity in same direction
    return (deltax * vrelx + deltay * vrely) > 0.0


cdef inline void collide(FLOAT *x1, FLOAT *v1,
                         FLOAT *x2, FLOAT *v2) nogil:

    cdef:
        float x1_minus_x2[2]
        float v1_minus_v2[2]
        float change_v1[2]
        float len_x1_m_x2, dot_v_x
        int dim
    # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional_collision_with_two_moving_objects
    for dim in range(2):
        x1_minus_x2[dim] = x1[dim] - x2[dim]
        v1_minus_v2[dim] = v1[dim] - v2[dim]
    len_x1_m_x2 = x1_minus_x2[0] * x1_minus_x2[0] + x1_minus_x2[1] * x1_minus_x2[1]
    dot_v_x = v1_minus_v2[0] * x1_minus_x2[0] + v1_minus_v2[1] * x1_minus_x2[1]
    for dim in range(2):
        change_v1[dim] = (dot_v_x / len_x1_m_x2) * x1_minus_x2[dim]

    for dim in range(2):
        v1[dim] -= change_v1[dim]
        v2[dim] += change_v1[dim]  # conservation of momentum


cdef void sub_update(FLOAT[:, ::1] XY,
                     FLOAT[:, ::1] V,
                     float R,
                     int i, int count,
                     UINT[:, ::1] Grid,
                     float grid_spacing,
                     omp_lock_t *locks) nogil:

    cdef:
        FLOAT *XY1, *XY2, *V1, *V2
        int j, k, dim
        float eps = 1e-5
        int my_gloc_x, my_gloc_y  # current Grid location for ball i
        int gridsize, ball_number, left, right, bottom, top

    # SUBPROBLEM 4: Add locking
    XY1 = &(XY[i, 0])
    V1 = &(V[i, 0])
    #############################################################
    # IMPORTANT: do not collide two balls twice.
    ############################################################
    # SUBPROBLEM 2: use the grid values to reduce the number of other
    # objects to check for collisions.

    # Instead of checking all i+1 remaining higher-ranked balls against
    # the ith ball, locate the ith ball on the Grid (my_gloc), and then check
    # neighboring grid spaces (up to two in each direction - a 5x5 grid
    # centered at my_gloc) for balls -- this replaces the O(n) inner loop
    # with a constant number (max. 24) of comparisons, thus making the
    # overall collision detection algorithm O(n)
    
    gridsize = <int>((1.0 / grid_spacing) + 1)
    my_gloc_x = <int>(XY[i, 0] / grid_spacing)
    my_gloc_y = <int>(XY[i, 1] / grid_spacing)

    # check neighboring grid cells, except cells out of boundaries,
    # own cells, or empty cells (empty cells are denoted by -1 in Grid,
    # or a very large number as an unsigned integer >> count)

    left = my_gloc_x - 2
    if left<0:
        left = 0

    right = my_gloc_x + 2
    if right>=gridsize:
        right = gridsize - 1 # inclusive
    
    bottom = my_gloc_y - 2
    if bottom<0:
        bottom = 0
    
    top = my_gloc_y + 2
    if top>=gridsize:
        top = gridsize - 1 # inclusive

    for j in range(left, right+1):
        for k in range(bottom, top+1):
            # check not own cell and Grid cell not empty
            if ((j!=my_gloc_x or k!=my_gloc_y) & (Grid[j,k]<count)):

                ball_number = <int>Grid[j, k]
                if ball_number > i:

                    # since we cycle through all balls (i takes on all
                    # ball indices) we should ignore balls with lower
                    # indices; this is done to avoid double counting
                    XY2 = &(XY[ball_number, 0])
                    V2 = &(V[ball_number, 0])
                    
                    if overlapping(XY1, XY2, R):
                        # SUBPROBLEM 4: Add locking

                    #####
                    #
                    # Lock-ordering

                    # We define a total ordering on the set of objects
                    # eligible for locking and use this ordering to choose
                    # the sequence of lock acquisition. In our case, v1 and
                    # v2 represent two entries of a larger velocities array,
                    # with i and ball_number representing the respective ball
                    # indexes; we always lock an entry of the velocities
                    # array associated with a lower ball index, before a
                    # higher ball index, otherwise we may encounter deadlock.
                    #
                    # Some domain knowledge would be helpful to investigate
                    # whether it is correct to force only two velocities to
                    # be processed at once. For example, if 3+ balls are
                    # overlapping, would we then be guaranteed that all
                    # velocities are changed correctly? Currently, it would
                    # seem that two balls may be sent off in different
                    # directions, causing some additional balls to continue
                    # on the same track when they might have reversed course.
                    # This may be looked into in future improvements.
                    
                    # Note: this portion of code is only called when
                    # ball_number > i (from above conditional). We use
                    # this fact below when acquiring locks.

                        acquire(&(locks[i]))
                        acquire(&(locks[ball_number])) 

                        ### critical section ###
                        if not moving_apart(XY1, V1, XY2, V2):
                            collide(XY1, V1, XY2, V2)

                        # give a slight impulse to help separate them
                        for dim in range(2):
                            V2[dim] += eps * (XY2[dim] - XY1[dim])
                        ### critical section ###

                        release(&(locks[ball_number])) 
                        release(&(locks[i]))

cpdef update(FLOAT[:, ::1] XY,
             FLOAT[:, ::1] V,
             UINT[:, ::1] Grid,
             float R,
             float grid_spacing,
             uintptr_t locks_ptr,
             float t):
    cdef:
        int count = XY.shape[0]
        int i, j, dim
        int chunks, n_threads
        FLOAT *XY1, *XY2, *V1, *V2

        int tempx, tempy

        # SUBPROBLEM 4: uncomment this code.
        omp_lock_t *locks = <omp_lock_t *> <void *> locks_ptr

    assert XY.shape[0] == V.shape[0]
    assert XY.shape[1] == V.shape[1] == 2

    # set parameters for prange loops
    chunks = int(count/4)
    n_threads = 4

    with nogil:
        # bounce off of walls
        #
        # SUBPROBLEM 1: parallelize this loop over 4 threads, with static
        # scheduling.
        for i in prange(count, num_threads=n_threads, schedule='static', 
                        chunksize=chunks):
            for dim in range(2):
                if (((XY[i, dim] < R) and (V[i, dim] < 0)) or
                    ((XY[i, dim] > 1.0 - R) and (V[i, dim] > 0))):
                    V[i, dim] *= -1

        # bounce off of each other
        #
        # SUBPROBLEM 1: parallelize this loop over 4 threads, with static
        # scheduling.
        for i in prange(count, num_threads=n_threads,
                        schedule='static', chunksize=chunks):
            #sub_update(XY, V, R, i, count, Grid, grid_spacing)
            #pass in set of locks
            sub_update(XY, V, R, i, count, Grid, grid_spacing, locks)

        # update positions
        #
        # SUBPROBLEM 1: parallelize this loop over 4 threads (with static
        #    scheduling).
        # SUBPROBLEM 2: update the grid values.
        for i in prange(count, num_threads=n_threads,
                        schedule='static', chunksize=chunks):

            # update grid values - delete old position for ball i from grid

            if XY[i, 0]<R:
                tempx = <int>(0)
            elif XY[i, 0] > 1.0 - R:
                tempx = <int>(1.0 / grid_spacing)
            else:
                tempx = <int>(XY[i, 0] / grid_spacing)

            if XY[i, 1]<R:
                tempy = <int>(0)
            elif XY[i, 1] > 1.0 - R:
                tempy = <int>(1.0 / grid_spacing)
            else:
                tempy = <int>(XY[i, 1] / grid_spacing)  

            Grid[tempx, tempy] = -1

            # new position
            for dim in range(2):
                XY[i, dim] += V[i, dim] * t

            # update index in grid values with new position for ball i;
            # for balls projected to be off the Grid; store ball in closest
            # Grid element

            if XY[i, 0]<R:
                tempx = <int>(0)
            elif XY[i, 0] > 1.0 - R:
                tempx = <int>(1.0 / grid_spacing)
            else:
                tempx = <int>(XY[i, 0] / grid_spacing)

            if XY[i, 1]<R:
                tempy = <int>(0)
            elif XY[i, 1] > 1.0 - R:
                tempy = <int>(1.0 / grid_spacing)
            else:
                tempy = <int>(XY[i, 1] / grid_spacing)    

            Grid[tempx, tempy] = i

def preallocate_locks(num_locks):
    cdef omp_lock_t *locks = get_N_locks(num_locks)
    assert 0 != <uintptr_t> <void *> locks, "could not allocate locks"
    return <uintptr_t> <void *> locks
