import numpy as np
from SwingyMonkey import SwingyMonkey


class Learner(object):
    '''
    This learner applies TD-value learning to determine what action to take
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

        # terminal state
        self.terminal = 'DEATH'

        # possible actions
        # 0 = swing downward
        # 1 = jump up
        self.actions = [0, 1]

        # values for TD learning
        self.values = dict()
        self.values[self.terminal] = -999999

        # transition function for TD learning
        # note: these are counts, not probabilities
        self.transitions = dict()

        # reward function for TD learning
        self.rewards_sum = dict()
        self.rewards_count = dict()
        self.rewards_sum[self.terminal] = {a: -999999 for a in self.actions}
        self.rewards_count[self.terminal] = {a: 1 for a in self.actions}

        # learning rate
        self.alpha_dynamic = False
        self.alpha = alpha

        # for dynamic learning rate
        self.observations = dict()

        # discount factor
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

    def get_value(self, state):
        '''
        Gets value for a state.
        Returns 0 if the state hasn't been seen before.
        Note: basis function should already have been applied to the state.
        '''

        # if state-action pair has been seen before, return value
        if state in self.values:
            return self.values[state]

        # otherwise return 0
        return 0.0

    def get_transitions(self, state, action):
        '''
        Gets transition probabilities for a given state-action pair
        Note: basis function should already have been applied to the states
        '''

        # if transition has been seen before, return probability
        if state in self.transitions:
            if action in self.transitions[state]:
                return self.transitions[state][action]

        # otherwise return an empty dictionary
        return {}

    def get_rewards(self, state, action):
        '''
        Gets reward for state-action pair
        Note: basis function should already have been applied to the state.
        '''

        # if state-action pair has been seen before, return average reward
        if state in self.rewards_count:
            if action in self.rewards_count[state]:
                reward_count = self.rewards_count[state][action]
                if reward_count > 0:
                    return self.rewards_sum[state][action] / reward_count

        # otherwise return 0
        return 0.0

    def get_argmax_value(self, state):
        '''
        Maximizes the value for a given state over possible actions.
        Returns 0 if the state hasn't been seen before.
        Note: basis function should already have been applied to the state.
        '''

        values = []

        for idx, action in enumerate(self.actions):
            
            # expected reward of taking an action from a given state
            value = self.get_rewards(state, action)

            # look up transitions for the state-action pair
            transitions = self.get_transitions(state, action)

            # process for conversion from counts to probabilities
            if len(transitions) > 0:
                total_counts = sum(transitions.values())

            # add expected value of new state
            for k, v in transitions.items():
                value += (v / total_counts) * self.get_value(k)

            # keep track of value of the action
            values.append(value)

        # return argmax
        return np.argmax(values)

        # NOTE: this makes performance worse - picking 0 is a better strategy
        # if both values are equal, pick one randomly
        # if len(set(values)) == 1:
        #     return np.random.choice(self.actions)
        # # otherwise return argmax
        # else:
        #     return np.argmax(values)

    def update_value(self):
        '''
        Updates value for previous state pair.
        '''

        # check that each of the parameters used is present
        if self.old_state is None: return
        if self.old_reward is None: return
        if self.new_state is None: return

        # check if states are already in dictionaries
        if self.old_state not in self.values:
            self.values[self.old_state] = 0.0
        if self.new_state not in self.values:
            self.values[self.new_state] = 0.0

        # update number of times the state has been observed
        if self.old_state not in self.observations:
            self.observations[self.old_state] = 0.0
        self.observations[self.old_state] += 1.0

        # learning rate
        if self.alpha_dynamic:
            use_alpha = 1.0 / self.observations[self.old_state] # dynamic
        else:
            use_alpha = self.alpha # static

        # temporal difference update
        value = self.values[self.old_state] # current value
        self.values[self.old_state] = value + use_alpha * (
            self.old_reward + self.gamma * self.values[self.new_state] - value)

    def update_transition(self):
        '''
        Updates transitions for last action.
        '''

        # check that each of the parameters used is present
        if self.old_state is None: return
        if self.old_action is None: return
        if self.new_state is None: return

        # check if states/actions are already in transition dictionary
        if self.old_state not in self.transitions:
            self.transitions[self.old_state] = dict()
        if self.old_action not in self.transitions[self.old_state]:
            self.transitions[self.old_state][self.old_action] = dict()
        if self.new_state not in self.transitions[self.old_state][self.old_action]:
            self.transitions[self.old_state][self.old_action][self.new_state] = 0.0

        # update count
        self.transitions[self.old_state][self.old_action][self.new_state] += 1.0

    def update_terminal_transition(self):
        '''
        Updates transitions for last action.
        '''

        # check that each of the parameters used is present
        if self.old_state is None: return
        if self.old_action is None: return

        # check if states/actions are already in transition dictionary
        if self.old_state not in self.transitions:
            self.transitions[self.old_state] = dict()
        if self.old_action not in self.transitions[self.old_state]:
            self.transitions[self.old_state][self.old_action] = dict()
        if self.terminal not in self.transitions[self.old_state][self.old_action]:
            self.transitions[self.old_state][self.old_action][self.terminal] = 0.0

        # update count
        self.transitions[self.old_state][self.old_action][self.terminal] += 1.0

    def update_reward(self):
        '''
        Update reward function for last state-action pair.
        '''

        # check that each of the parameters used is present
        if self.old_state is None: return
        if self.old_action is None: return
        if self.old_reward is None: return

        # check if state-action pair is already in dictionary
        if self.old_state not in self.rewards_sum:
            self.rewards_sum[self.old_state] = dict()
            self.rewards_count[self.old_state] = dict()
        if self.old_action not in self.rewards_sum[self.old_state]:
            self.rewards_sum[self.old_state][self.old_action] = 0.0
            self.rewards_count[self.old_state][self.old_action] = 0.0

        # update for last observation
        self.rewards_sum[self.old_state][self.old_action] += self.old_reward
        self.rewards_count[self.old_state][self.old_action] += 1.0

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
            self.new_action = np.random.choice(self.actions) # randomly choose an action
        else:
            self.new_action = self.get_argmax_value(self.new_state) # choose optimal action

        # return chosen actions
        return self.new_action

    def reward_callback(self, reward):
        '''
        Updates the reward from the immediately previous time step.
        '''

        # keep track of previous reward
        self.old_reward = reward

        # update value
        self.update_value()

        # update transition function
        self.update_transition()

        # update reward function
        self.update_reward()


def run_games(learner, hist, iters=100, t_len=100):
    '''
    Driver function to simulate learning by having the agent play a sequence of games.
    '''

    for ii in range(iters):

        # make a new monkey object
        swing = SwingyMonkey(sound=False,                  # don't play sounds
                             text="Epoch %d" % (ii),       # display the epoch on screen
                             tick_length = t_len,          # make game ticks super fast
                             action_callback=learner.action_callback,
                             reward_callback=learner.reward_callback)

        # pass the screen dimensions to the agent
        learner.update_specs(swing.screen_height, swing.screen_width)

        # loop until you hit something
        while swing.game_loop():
            pass

        # update transition to terminal state
        learner.update_terminal_transition()

        # save score history
        hist.append(swing.score)
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
    agent = Learner(alpha=0.00, gamma=0.00, epsilon=0.00)

    # empty list to save history
    hist = []

    # run games
    score = run_games(agent, hist, iters=100, t_len=0)

    # save history
    np.save('hist-td', np.array(hist))
