# annealing.py
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
# runs Simulated Annealing algorithm for MasterMind
# Reference: Bernier et al. "Solving MasterMind using GAs and simulated
#     annealing: a case of dynamic constraint optimization"

'''
Example:

>>> python annealing.py

Code successfully initialized to  [0 5 0 4]

guess #1 of 10: you guessed  [3, 2, 3, 0]
You have 0 right item(s) in the right place, and
  1 right item(s) but in the wrong place

accepted better or equal, temperature: 6
guess #2 of 10: you guessed  [3, 2, 3, 4]
You have 1 right item(s) in the right place, and
  0 right item(s) but in the wrong place

accepted worse (random), temperature: 5.88
guess #3 of 10: you guessed  [3, 3, 2, 0]
You have 0 right item(s) in the right place, and
  1 right item(s) but in the wrong place

accepted better or equal, temperature: 5.7624
guess #4 of 10: you guessed  [5, 4, 0, 5]
You have 1 right item(s) in the right place, and
  2 right item(s) but in the wrong place

accepted better or equal, temperature: 4.34278632355
guess #5 of 10: you guessed  [0, 0, 5, 5]
You have 1 right item(s) in the right place, and
  2 right item(s) but in the wrong place

accepted worse (random), temperature: 3.08043286517
guess #6 of 10: you guessed  [5, 0, 4, 4]
You have 1 right item(s) in the right place, and
  2 right item(s) but in the wrong place

accepted better or equal, temperature: 0.082809335026
guess #7 of 10: you guessed  [0, 5, 0, 4]
You have 4 right item(s) in the right place
You win!
'''

import MMboard as mm

import numpy as np
import copy
import matplotlib.pyplot as plt


class SAsim():

    '''An instance of a simulated annealing solution to solve Mastermind.

    These methods implement simulated annealing (SA)
    Reference: Bernier et al. "Solving MasterMind using GAs and simulated
       annealing: a case of dynamic constraint optimization"

    Bernier suggests SA finds best solution within a given time constraint
    but solution is suboptimal; without a time constraint, the algorithm
    reduces to a random search.'''

    def __init__(self):
        # store previous guesses, along with response
        # key is the string sequence, values is the (b, w) tuple as returned
        # by guess_code;
        # supports up to N=10 digits (0-indexed) per position
        self._prev_guesses = {}

        self._best_guess = None  # stores best guess so far
        self._best_resp = None  # stores best response so far

    def _objective_function(self, guess):
        '''Implement Bernier objective function.

        `guess` is in the form of a list or numpy array.

        "Each combination is compared with the previously played guess, the
        number of different white and black pegs are computed and added to the
        cost... In this way, the cost increases with the number of unsatisfied
        rules."

        The idea here is that given a new guess, would all the different
        responses for the previous attempts be satisfied if the new guess were
        actually the correct answer?  If so, then the new guess could possibly
        be the secret code. Otherwise, it cannot possibly be the new code,
        but may be close to it.'''

        assert self._sa._codeOK(guess)
        C = 0

        for pg in self._prev_guesses:
            # get what response for a code would have been if the
            # guess is actually the right code, for each previous guess
            prop_answer = [int(digit) for digit in list(pg)]
            b, w = self._sa.check_guess(guess=guess, answer=prop_answer)
            assert (b + w) <= self._sa._L

            diffw = self._prev_guesses[pg][1] - w
            diffb = self._prev_guesses[pg][0] - b
            C += abs(diffw) + abs(diffw + diffb)

        return C

    def _change_guess(self, guess, repeats=5):
        '''Takes in a guess as a list of digits, and performs a permutation
        (change positions of a randomly chosen pair of digits) and/or a mutation
        (change value of randomly chosen digit).

        `repeats` is the step size (# of changes before returning new guess)'''

        assert self._sa._codeOK(guess)
        guess_prime = copy.deepcopy(guess)

        for i in xrange(max(repeats, 1)):

            # permutation
            # do not permutate if all but one digits are already right
            if not ((self._best_guess == guess) and
                    (self._best_resp[0] >= (self._sa._L - 1))):

                idx1, idx2 = np.random.choice(len(guess), size=2, replace=False)

                temp = guess_prime[idx1]
                guess_prime[idx1] = guess_prime[idx2]
                guess_prime[idx2] = temp

            # mutation
            # do not mutate if all digits found but in wrong spots
            if not((self._best_guess == guess) and
                   ((self._best_resp[0] + self._best_resp[1]) == self._sa._L)):

                idx3 = np.random.choice(len(guess))  # position
                col = np.random.choice(self._sa._C)  # proposed new color
                while idx3 == col:
                    col = np.random.choice(self._sa._C)  # try again

                guess_prime[idx3] = col

                # if only one digit is off (i.e. w=1 and b is the maximum
                # otherwise), don't mutate more than one character
                if ((self._best_guess == guess) and
                    (self._best_resp[0] >= (self._sa._L - 1))):
                    break

        return guess_prime

    def _closeness_score(self, resp):
        # the higher score, the more correct the answer
        # we cannot really use this as the objective function, since we need
        # to actually make a guess before getting this response (it is based
        # on the actual code and only attainable by committing a guess);
        # but we can use this to identify the final best answer for reporting
        # if we did not guess the correct answer in the limited number of
        # tries/time

        # inspired by the score for the genetic algorithm, we start with the
        # following:
        # score: 10 * black + 1 * white
        # weights correct digit in correct position more heavily

        # response is in the form of a (b, w) tuple
        # however, we modify this score so that if all the correct digits have
        # been found (but answer is wrong), this is just as good as finding all
        # but one correct digits as we can reduce the
        # dimension of the search to just one type (mutation OR permutation)

        if (resp[0] != self._sa._L) and ((resp[0] + resp[1]) == self._sa._L):
            return (self._sa._L - 1) * 10

        return resp[0] * 10 + resp[1]

    def sa(self, guess, resp, init_temp, thermostat, ftol, itol, otol, k):
        '''Perform simulated annealing.

        Inputs:
        guess: the initial guess
        resp: the response returned from the MasterMind solver for that guess
        init_temp: the initial temperature for the SA algorithm
        thermostat: the rate at which temperature is decreased
        itol: a proxy for the maximum time SA can run to solve the game
              in SA iterations (which is larger than number of guesses made)
        ftol, otol: other stopping criteria, not currently used
        k: temperature tuning parameter

        Returns:
        A tuple containing the (best guess before time expired,
                                the (b, w) response for the best guess,
                                the number of iterations<=itol performed) '''

        obj_values = []  # stores objective function values from successive runs
        curr_guess = copy.deepcopy(guess)

        prev_E = 3 * self._sa._L  # arbitrarily large initial "energy"
        obj_values.append(prev_E)
        temperature = init_temp

        best_score = self._closeness_score(resp)  # store best objective function seen so far
        self._best_guess = guess  # store initial guess as corresponding best guess
        self._best_resp = resp  # store its response as corresponding best response

        it = 1  # acceptances counter (i.e. actual guesses made)
        atp = 1  # total number of iterations

        while True:

            L = np.floor(temperature).astype(int)  # step size
            # L = np.floor(np.exp(temperature)).astype(int)  # alternative step size
            # L = np.floor(np.sqrt(temperature)).astype(int)  # alternative step size
            # L = np.floor(np.log(temperature)).astype(int)  # alternative step size

            propose_guess = self._change_guess(curr_guess, L)

            # check whether proposed guess has already been guessed
            pg_str = ''.join(map(str, propose_guess))
            while pg_str in self._prev_guesses:
                propose_guess = self._change_guess(curr_guess)  # guess again
                pg_str = ''.join(map(str, propose_guess))

            new_E = self._objective_function(propose_guess)
            delta_E = new_E - prev_E

            # if we find something of equal (not just strictly lower) cost,
            # we try that as well as the corresponding combination could be good
            if ((delta_E <= 0) or
                (np.random.rand() < np.exp(- 1.0 * delta_E / (k * temperature)))):
                # how choice was made
                if delta_E <= 0:
                    if not(self._sa._nooutput):
                        print "accepted better or equal, temperature:", temperature
                else:
                    if not(self._sa._nooutput):
                        print "accepted worse (random), temperature:", temperature

                # accept proposal from which to make next guess
                curr_guess = propose_guess
                obj_values.append(new_E)
                prev_E = new_E
                it += 1

                # actually make the guess
                response = self._sa.guess_code(propose_guess)

                # keep track of best guess
                if self._closeness_score(response) >= best_score:
                    best_score = self._closeness_score(response)
                    self._best_guess = curr_guess
                    self._best_resp = response

                # If the response is four colored pegs, the game is won,
                # the algorithm terminates.
                # If maximum number of tries reached, the algorithm terminates.
                if (((response is not None) and response[0]==self._sa._L) or
                    self._sa.gameover):
                    # print details of best guess when game has ended
                    if response[0] != self._sa._L:
                        if not(self._sa._nooutput):
                            print 'best guess', self._best_guess, self._best_resp, it
                            print 'actual', self._sa._code
                    break

                # Otherwise, cache the response
                self._prev_guesses[pg_str] = response

            atp += 1

            # temperature adjustment and reannealing
            temperature = thermostat * temperature
            if ((temperature <= 2) and
                (self._closeness_score(response) < best_score)):
                # we implemented a variation of reannealing here
                # if we jumped to a new guess that has a score that is
                # worse than the current best score, then we have to jump
                # around more to further explore the space (i.e. "reheat")
                # so we reset to a higher fraction of the initial temperature
                temperature = init_temp * 0.8

            # termination conditions
            if atp > itol:
                if not(self._sa._nooutput):
                    print 'itol: maximum iterations reached'
                    print 'best guess', self._best_guess, self._best_resp, it
                    print 'actual', self._sa._code
                break

        if not(self._sa._nooutput):
            print "plotted"
            plt.figure()
            plt.plot(obj_values)
            plt.title("Objective function")
            plt.show()

        return self._best_guess, self._best_resp, it

    def runSA(self, cl=4, nc=6, code=None, silent=False):
        '''Driver: Set up board and run SA algorithm. '''

        # if code is provided, it must be in the form of a list or 1-D numpy array
        self._sa = mm.MMboard(codelength=cl, numcolors=nc, suppress_output=silent)
        if code is None:
            self._sa.set_code()
        else:
            self._sa.set_code(code)

        # initial guess
        sa_guess = list(np.random.randint(0, nc, cl))
        # play the guess to get a response of colored (b) and white pegs.
        response = self._sa.guess_code(sa_guess)

        # If the response is four colored pegs, the game is won, the algorithm
        # terminates.
        # If maximum number of tries reached, the algorithm terminates.
        if ((response is not None) and response[0] == cl) or self._sa.gameover:
            return 1

        # Otherwise, cache the response
        self._prev_guesses[''.join(map(str, sa_guess))] = response

        # we fiddled around with these parameters
        init_temp = 6
        thermostat = 0.98
        k = 0.2  # try slightly bigger fractions for larger spaces
        itol = 10000  # this is a proxy for allowable execution time

        # output is in the form of best guess, best response, number of guesses
        output = self.sa(sa_guess, response, init_temp, thermostat, 0, itol, 0, k)

        return output[2]  # number of guesses

if __name__ == "__main__":
    s = SAsim()
    s.runSA() # same as runSA(cl=4, nc=6, silent=False)
