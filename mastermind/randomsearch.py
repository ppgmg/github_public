# randomsearch.py
# v 1.0  27 April 2016 [KL]

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# AM 207 - Stochastic Methods for Data Analysis, Inference and Optimization
#
# Course Project
#
######################

# example driver for MasterMind class:
# runs "random search with constraints" algorithm for MasterMind
# Reference: Bernier et al. "Solving MasterMind using GAs and simulated
#     annealing: a case of dynamic constraint optimization"

'''
Example:

>>> python randomsearch.py

Code successfully initialized to  [2 2 1 2]

guess #1 of 10: you guessed  [1, 3, 3, 5]
You have 0 right item(s) in the right place, and
  1 right item(s) but in the wrong place

guess #2 of 10: you guessed  [4, 0, 0, 1]
You have 0 right item(s) in the right place, and
  1 right item(s) but in the wrong place

guess #3 of 10: you guessed  [5, 4, 2, 4]
You have 0 right item(s) in the right place, and
  1 right item(s) but in the wrong place

guess #4 of 10: you guessed  [2, 2, 1, 2]
You have 4 right item(s) in the right place
You win!
'''

import MMboard as mm

import itertools
import numpy as np

def random_search(cl=4, nc=6, code=None, silent=False):
    # implements Random-Search with constraints
    # expanded for arbitrary code lengths and alphabet
    # https://en.wikipedia.org/wiki/Mastermind_(board_game)

    # NOTE: we are using a 0-index
    # if code is provided, it must be in the form of a list or 1-D numpy array

    # Returns: total number of guesses

    rs = mm.MMboard(codelength=cl, numcolors=nc, suppress_output=silent)
    if code is None:
        rs.set_code()
    else:
        rs.set_code(code)

    n_guesses = 0

    # Create the set S of all possible codes (1111, 1112 ... 6665, 6666)
    S = {}  # index is the string sequence, value is a cl-element tuple
    digits = list(np.arange(nc))
    for i in itertools.product(digits, repeat=cl):
        S[''.join(map(str, list(i)))] = list(i)
    assert len(S) == nc**cl

    possible_guesses = S.copy()  # keep track of list of possible guesses

    # Start with a random guess
    assert nc >= 2
    rs_guess = list(np.random.randint(0, nc, cl))

    while True:
        # this is not an infinite loop -
        # maximum iterations governed by max number of possible guesses

        # delete current guess from possible guesses
        del possible_guesses[''.join(map(str, rs_guess))]

        # Play the guess to get a response of colored (b) and white pegs.
        response = rs.guess_code(rs_guess)
        n_guesses += 1

        # If the response is four colored pegs, the game is won, the algorithm
        #  terminates.
        # If maximum number of tries reached, the algorithm terminates.
        if ((response is not None) and response[0]==cl) or rs.gameover:
            return n_guesses

        # Otherwise, remove from S any code that would not give the same response
        #   if it (the guess) were the code.
        # print "number of keys to check:", len(S)
        for code in S.keys():
            # Uses class' built-in check_guess function
            temp = rs.check_guess(guess=S[code], answer=rs_guess)
            if temp!=response:
                del S[code]

        # For each possible guess, that is, any unused code in S,
        # select a code at random as the next guess
        if len(S)==1:
            rs_guess = S.values()[0]
        else:
            selection = np.random.randint(len(S))
            rs_guess = S.values()[selection]

if __name__ == "__main__":
    random_search()  # same as random_search(cl=4, nc=6, silent=False)
