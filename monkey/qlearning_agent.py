import numpy as np
from SwingyMonkey import SwingyMonkey


class Learner(object):
    '''
    This learner applies Q-learning to determine what action to take
    at each state.
    '''

    def __init__(self, gamma, alpha, epsilon):

        # keep track of previous step
        self.old_state = None
        self.old_action = None
        self.old_reward = None

        # keep track of current step
        self.new_state = None
        self.new_action = None

        # possible actions
        # 0 = swing downward
        # 1 = jump up
        self.actions = [0, 1]

        # q-values for online model-free learning
        self.qvalues = dict()

        # parameters for q-learning
        self.alpha = alpha
        self.gamma = gamma

        # parameter for epsilon-greedy
        self.epsilon = epsilon

    def update_specs(self, height, width):
        '''
        Save game specs for discretization of state space.
        '''

        self.height_max = height
        self.width_max = width

    def reset(self):

        # reset previous step
        self.old_state = None
        self.old_action = None
        self.old_reward = None

        # reset current step
        self.new_state = None
        self.new_action = None

    def basis_function(self, state):
        '''
        Converts continuous state space to a manageable discrete state space.
        '''

        # should never be true
        if state is None:
            return None

        '''
        Challenges:
        (1) the monkey arbitrarily jumps really high thus smashing his head
            at the top, and we cannot control how high he jumps,
            we can only jump or not
        (2) because the rewards for hitting the top or hitting the bottom
            are the same, we cannot train to differentiate these events

        *** Goal is to reduce state space for faster training.
        There is a tradeoff between training time and accuracy.
        Rather than settling for many equal size bins, let's see if we
        can split up space unevenly in a way that still might make sense,
        and that is customized for each feature.
        '''

        # 1. let's try measuring horizontal distance relative to gap width
        gap_size = state['tree']['top'] - state['tree']['bot']

        # the farther away monkey is from the gap, the less likely he is
        # going to have to take an action; the important distance is not an
        # absolute one - smaller gaps require the monkey to take action closer
        # to the gap, whereas larger gaps do not require immediate action
        # try (4) states
        if state['tree']['dist'] > 2 * gap_size:
            horiz_states = "very far"
        elif state['tree']['dist'] > 1.5 * gap_size:
            horiz_states = "far"
        elif state['tree']['dist'] > gap_size:
            horiz_states = "close"
        else:
            horiz_states = "vclose"

        # 2. let's divide monkey's velocity into (2) states based on direction
        # of travel; we may not even need this as there is no suggestion that
        # the jumping motion will be different depending on velocity, but
        # we include just in case
        if state['monkey']['vel'] > 0:
            moving = "up"
        else:
            moving = "down"

        # 3. check where monkey's center of mass is with respect to the gap
        center = (state['monkey']['top'] + state['monkey']['bot'])/2
        pos = (center - state['tree']['bot']) * 1.0 / gap_size
        # if the top of a floor stump is 0, and the bottom of a hanging stump
        # is 1, where is the monkey on the scale of [0, 1]?
        # note that we can get a number outside this range if the monkey's
        # center is no longer aligned with the gap
        # this seems like an important variable (most likely to be correlated
        # with whether or not a collision will happen) and the whole range
        # is likely to be covered in a few iterations, so we can afford more
        # bins while still expecting relatively quick training time

        bins = 10  # split this range into deciles
        pos = int(pos * bins)
        if pos > bins:
            pos = bins  # ceil
        elif pos < 0:
            pos = 0  # floor
        else:
            pass  # no change

        # 4a. check if close to border (try two body lengths)
        # this is fine tuning; likely if the monkey is close to the top or
        # bottom border, he will not be aligned with the gap anyway
        tol = 2.0 * (state['monkey']['top'] - state['monkey']['bot'])
        if (self.height_max - state['monkey']['top']) < tol:
            border = "topclose"
        elif state['monkey']['bot'] < tol:
            border = "bottomclose"
        else:
            border = "safe"

        # 4b. try tracking monkey's absolute position (3 levels)
        # may help to address possible asymmetry if any between
        # impulse applied to jumping and rate of drop;
        # range likely to be evenly covered so should not stall training
        if center < (0.3 * self.height_max):
            monkeypos = "lo"
        elif center < (0.6 * self.height_max):
            monkeypos = "mid"
        else:
            monkeypos = "hi"

        # Note: states = 4 x 2 x 10 x 3 x 3 = 720
        # This is comparable to keeping the original 6 state variables
        # and splitting each into 3 bins (729), but we get a lot more
        # discrimination where it counts, and we are not just dividing up wide
        # swaths of pixel space without purpose
        return (horiz_states, moving, pos, border, monkeypos)

    def get_qvalue(self, state, action):
        '''
        Gets q-value for a state-action pair.
        Returns 0 if the state-action pair hasn't been seen before.
        Note: basis function should already have been applied to the state.
        '''

        if (state in self.qvalues) and (action in self.qvalues[state]):
            return self.qvalues[state][action]

        # otherwise return 0
        return 0.0

    def get_max_qvalue(self, state):
        '''
        Maximizes the q-value for a given state over possible actions.
        Returns 0 if the state hasn't been seen before.
        Note: basis function should already have been applied to the state.
        '''

        # q-value of all possible actions
        qvals = [self.get_qvalue(state, action) for action in self.actions]

        # return maximum
        return max(qvals)

    def get_argmax_qvalue(self, state):
        '''
        Maximizes the q-value for a given state over possible actions.
        Returns 0 if the state hasn't been seen before.
        Note: basis function should already have been applied to the state.
        '''

        # q-value of all possible actions
        qvals = [self.get_qvalue(state, action) for action in self.actions]

        # return argmax
        return np.argmax(qvals)

        # NOTE: this makes performance worse - picking 0 is a better strategy
        # # if both values are equal, pick one randomly
        # if len(set(qvals)) == 1:
        #     return np.random.choice(self.actions)
        # # otherwise return argmax
        # else:
        #     return np.argmax(qvals)

    def update_qvalue(self):
        '''
        Updates q-value for previous state-action pair.
        '''

        # check that each of the parameters used is present
        if self.old_state is None:
            return
        if self.old_action is None:
            return
        if self.old_reward is None:
            return
        if self.new_state is None:
            return

        # check if state-action pair is already in q-value dictionary
        if self.old_state not in self.qvalues:
            self.qvalues[self.old_state] = dict()
        if self.old_action not in self.qvalues[self.old_state]:
            self.qvalues[self.old_state][self.old_action] = 0.0

        # increase gamma with time
        if self.gamma < 1.0:
            self.gamma += 0.000001

        # temporal difference update
        qvalue = self.qvalues[self.old_state][self.old_action]  # current value
        self.qvalues[self.old_state][self.old_action] = qvalue + self.alpha * (
            (self.old_reward + self.gamma * self.get_max_qvalue(self.new_state)) - qvalue)

    def action_callback(self, state):
        '''
        Carries out temporal difference update and selects next action.
        '''

        # keep track of previous/new state
        self.old_state = self.new_state
        self.new_state = self.basis_function(state)

        # keep track of action
        self.old_action = self.new_action

        # choose new action using epsilon-greedy
        if np.random.rand() < self.epsilon:
            # randomly choose an action
            self.new_action = np.random.choice(self.actions)
        else:
            # choose optimal action
            self.new_action = self.get_argmax_qvalue(self.new_state)

        # return chosen action
        return self.new_action

    def reward_callback(self, reward):
        '''
        Updates the reward from the immediately previous time step.
        '''

        # keep track of previous reward
        self.old_reward = reward

        # update q-value
        self.update_qvalue()


def run_games(learner, hist, iters=100, t_len=100):
    ''' Driver function to simulate learning by having the agent play a
    sequence of games.'''

    for ii in range(iters):

        # make a new monkey object
        swing = SwingyMonkey(sound=False,             # don't play sounds
                             text="Epoch %d" % (ii),  # display epoch on screen
                             tick_length=t_len,       # make game ticks fast
                             action_callback=learner.action_callback,
                             reward_callback=learner.reward_callback)

        # pass the screen dimensions to the agent
        learner.update_specs(swing.screen_height, swing.screen_width)

        # loop until you hit something
        while swing.game_loop():
            pass

        # save score history
        hist.append(swing.score)
        output = (ii, swing.score, np.max(hist), learner.gamma)
        print 'Epoch %i: current score %i; best score %i' % (ii, swing.score, np.max(hist))

        # reset the state of the learner
        learner.reset()

    # display score history and stats
    print '----------'
    print 'Parameters: %0.2f alpha; %0.2f gamma; %0.2f epsilon' % (learner.alpha, learner.gamma, learner.epsilon)
    print 'Score history:', hist
    print 'Best score:', np.max(hist)
    print 'Average score:', np.mean(hist)
    print '----------'

    return np.max(hist)


if __name__ == '__main__':

    # select agent
    agent = Learner(alpha=0.01, gamma=0.7, epsilon=0.0)

    # empty list to save history
    hist = []

    # run games
    score = run_games(agent, hist, iters=100, t_len=0)

    # save history
    np.save('hist-q', np.array(hist))
