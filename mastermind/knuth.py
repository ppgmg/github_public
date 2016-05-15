# knuth.py
# v 1.0  20 April 2016 [KL]

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# AM 207 - Stochastic Methods for Data Analysis, Inference and Optimization
#
# Course Project
#
######################

# example driver for MasterMind class:
# runs Knuth solver for MasterMind

'''
Example:

>>> python knuth.py

Code successfully initialized to  [1 1 2 0]

guess #1 of 10: you guessed  [0, 0, 1, 1]
You have 0 right item(s) in the right place, and
  3 right item(s) but in the wrong place

guess #2 of 10: you guessed  [5, 1, 3, 0]
You have 2 right item(s) in the right place, and
  0 right item(s) but in the wrong place

guess #3 of 10: you guessed  [2, 1, 0, 0]
You have 2 right item(s) in the right place, and
  1 right item(s) but in the wrong place

guess #4 of 10: you guessed  [1, 1, 2, 0]
You have 4 right item(s) in the right place
You win!
'''

import MMboard as mm

import numpy as np
import itertools
from collections import Counter


def knuth(cl=4, nc=6, code=None, silent=False):
    # implements Knuth's Five-Guess Algorithm
    # expanded for arbitrary code lengths and alphabet
    # https://en.wikipedia.org/wiki/Mastermind_(board_game)
    # Numbered comments below are from the Wikipedia article.

    # NOTE: we are using a 0-index
    # if code is provided, it must be in the form of a list or 1-D numpy array

    # Returns: total number of guesses

    k = mm.MMboard(codelength=cl, numcolors=nc, suppress_output=silent)
    if code is None:
        k.set_code()  # set random
    else:
        k.set_code(code)

    n_guesses = 0

    # "1. Create the set S of 1296 possible codes (1111, 1112 ... 6665, 6666)"
    S = {}  # index is the string sequence, value is a cl-element tuple
    digits = list(np.arange(nc))
    for i in itertools.product(digits, repeat=cl):
        S[''.join(map(str, list(i)))] = list(i)
    assert len(S) == nc**cl

    possible_guesses = S.copy()  # keep track of list of possible guesses

    # "2. Start with initial guess 1122"
    assert nc >= 2
    if cl == 4:
        knuth_guess = [0, 0, 1, 1]  # 0-indexed
    else:
        # n.b. random choice may be suboptimal
        knuth_guess = list(np.random.randint(0, nc, cl))

    # "7. loop"
    while True:
        # this is not an infinite loop -
        # maximum iterations governed by max number of possible guesses

        # delete current guess from possible guesses
        del possible_guesses[''.join(map(str, knuth_guess))]

        # "3. Play the guess to get a response of colored (b) and white pegs"
        response = k.guess_code(knuth_guess)
        n_guesses += 1

        # "4. If the response is four colored pegs, the game is won,
        #    the algorithm terminates.
        #    Also if maximum number of tries reached, the algorithm terminates"
        if ((response is not None) and response[0] == cl) or k.gameover:
            return n_guesses

        # "5. Otherwise, remove from S any code that would not give the same
        #    response if it (the guess) were the code"
        for code in S.keys():
            # Uses class' built-in check_guess function
            temp = k.check_guess(guess=S[code], answer=knuth_guess)
            if temp != response:
                del S[code]

        # "6. For each possible guess, that is, any unused code of the 1296 not
        #    just those in S, calculate how many possibilities in S would be
        #    eliminated for each possible colored/white peg score. The score of
        #    a guess is the minimum number of possibilities it might eliminate
        #    from S. A single pass through S for each unused code of the 1296
        #    will provide a hit count for each colored/white peg score found;
        #    the colored/white peg score with the highest hit count will
        #    eliminate the fewest possibilities; calculate the score of a guess
        #    by using
        #    "minimum eliminated" = "count of elements in S" - "highest hit count".
        #    From the set of guesses with the maximum score, select one as the
        #    next guess, choosing a member of S whenever possible"

        if len(S) == 1:
            knuth_guess = S.values()[0]
        else:
            # use of collection counter
            # inspired by http://stackoverflow.com/questions/20298190/mastermind-minimax-algorithm
            key = lambda g: max(Counter(k.check_guess(g, item) for item in S.values()).values())
            # secondary sort by choosing member of S
            # inspired by https://docs.python.org/2/howto/sorting.html
            secondary_sort = sorted(possible_guesses.values(), key=lambda x: x not in S.values())
            knuth_guess = min(secondary_sort, key=key)

if __name__ == "__main__":
    knuth()  # same as knuth(cl=4, nc=6, silent=False)
