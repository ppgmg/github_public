# MMboard.py
# v 1.0  20 April 2016 [KL]

######################
#
# Submission by Kendrick Lo (Harvard ID: 70984997) for
# AM 207 - Stochastic Methods for Data Analysis, Inference and Optimization
#
# Course Project
#
######################

# implements MasterMind game instances

'''
Usage:
a = MMboard()                 # customizable
a.set_code()                  # or a.set_code([2, 1, 4, 4]) for custom
a.guess_code([0, 1, 2, 4])    # up to default of 10 tries

Example:
>>> a = MMboard()
>>> a.set_code(showcode=True)
Code successfully initialized to  [2 1 4 4]
>>> a.guess_code([0, 1, 2, 4])  # returns (2, 1)
guess #1 of 10: you guessed  [0, 1, 2, 4]
You have 2 right item(s) in the right place, and
  1 right item(s) but in the wrong place
>>> a.guess_code([0, 3, 2, 4])  # returns (1, 1)
guess #2 of 10: you guessed  [0, 3, 2, 4]
You have 1 right item(s) in the right place, and
  1 right item(s) but in the wrong place
>>> a.guess_code([0, 3, 2, 9])  # returns None
  [Error] please enter a list of 4 integers from 0 to 5. try again
>>> a.guess_code([1, 1, 1, 1])  # returns (1, 0)
guess #3 of 10: you guessed  [1, 1, 1, 1]
You have 1 right item(s) in the right place, and
  0 right item(s) but in the wrong place
>>> a.guess_code([2, 1, 4, 4])  # returns (4, 0)
guess #6 of 10: you guessed  [2, 1, 4, 4]
You have 4 right item(s) in the right place
You win!
'''

import numpy as np
import sys


class MMboard:
    '''An instance of a MasterMind board.

    The object of the game is to guess the hidden code of length L,
    where each code element is any one of C characters.

    In response to a guess of the code, if the code is incorrect,
    a response (b, w) is provided; b represents the number of
    characters where the correct character is provided in the
    correct position, whereas w represents the number of characters
    that are in the code but are in the wrong position (i.e. the
    number of characters that are actually in the code but are not
    in the position guessed).

    The game continues until the correct code is guessed, or until
    a predefined number of allowable tries have been exhausted.

    Note: Currently supports numcolors <= 10. '''

    def __init__(self, codelength=4, numcolors=6, max_tries=10,
                 suppress_output=False):

        assert (codelength >= 1) and (numcolors >= 1)
        assert (max_tries >= 1) and (max_tries <= 10)

        self._L = codelength
        self._C = numcolors
        self._N_iters = max_tries
        self._nooutput = suppress_output

        self._code = np.zeros(self._L)  # contains the code

        self.n_guessed = 0  # number of guesses tried
        self.gameover = False

    def _codeOK(self, cc):
        '''Helper function to check that inputs for code are in
        proper form. '''

        try:
            init = np.array([int(item) for item in cc])
        except:
            raise ValueError('Code not in the form of a list/array of length ' + str(self._L))

        if len(init) != self._L:
            raise ValueError('Code not of length ' + str(self._L))

        if not all(isinstance(item, int) for item in init):
            raise ValueError('Each character must be an integer, between 0 and ' + str(self._C - 1))

        if not((init >= 0).all() and (init <= self._C - 1).all()):
            raise ValueError('Each integer must be between 0 and ' + str(self._C - 1))

        return True

    def set_code(self, custom=None, showcode=True):
        '''Initalize/reset the code.

        Can set the code manually (provide a list or array of length L)
        or set one at random (default).

        Example: myboard.set_code([0, 1, 2, 3])

        showcode: whether or not the code being set is displayed
        '''

        if (custom is not None) and self._codeOK(custom):
            self._code = np.array([int(item) for item in custom])
        else:
            # each element is [0, C)
            self._code = np.random.randint(0, self._C, size=self._L)

        if showcode and (not self._nooutput):
            print "Code successfully initialized to ", self._code, "\n"
        elif not self._nooutput:
            print "Code successfully initialized. Good luck.\n"

        self.n_guessed = 0  # reset guess counter
        self.gameover = False

    def check_guess(self, guess, answer):
        '''Process a guess given the correct code.

        Take a guess in the form of a list of integers, and returns
        (number of characters in the correct position,
         number of characters in the wrong position but elsewhere in code).

        Usually, the answer will be the secret code (self._code), but this
        method can be used to compare any guess to any answer.

        Example: myboard.guess_code([0, 1, 2, 3], self._code)
        Returns: (1, 1)  # self._code is [2 1 4 4] '''

        # counters
        corpos = 0
        wrongpos = 0
        # track non-counted characters
        code_left = []
        guess_left = []

        # check for correct digit in correct place
        for i, digit in enumerate(answer):
            if digit == guess[i]:
                corpos += 1
            else:
                code_left.append(digit)
                guess_left.append(guess[i])

        assert len(code_left) == len(guess_left)

        if len(code_left) > 0:
            # check for correct digit in wrong place
            for digit in code_left:
                if digit in guess_left:
                    wrongpos += 1
                    guess_left.remove(digit)  # removes only one occurrence

        return (corpos, wrongpos)

    def guess_code(self, guess):
        '''Entry method to process guess, with a check to see if number of
        guesses has been exceeded, or code guessed correctly.

        If game is over, self.gameover is set to True.

        Returns: a tuple - (number of characters in the correct position,
                            number of characters in the wrong position but
                            elsewhere in code);
                  None if there was an error in the guess; or
                  -1 if game is over'''

        if not self.gameover:
            try:
                assert self._codeOK(guess)
                self.n_guessed += 1
                if not self._nooutput:
                    print "guess #" + str(self.n_guessed) + " of " + str(self._N_iters) + ": you guessed ", guess
                    sys.stdout.flush()
            except:
                if not self._nooutput:
                    print "  [Error] please enter a list of %i integers from 0 to %i. try again" % (self._L, self._C - 1)
                return None

            # get response
            b, w = self.check_guess(guess=guess, answer=self._code)
            assert (b + w) <= self._L

            if b == self._L:
                if not self._nooutput:
                    print "You have %i right item(s) in the right place" % b
                    print "You win!"
                self.gameover = True
                return (b, w)

            if not self._nooutput:
                print "You have %i right item(s) in the right place, and" % b
                print "  %i right item(s) but in the wrong place\n" % w

            if self.n_guessed == self._N_iters:
                if not self._nooutput:
                    print "Game over. The correct code was", self._code
                self.gameover = True

            return (b, w)

        # else
        return -1  # game already over
