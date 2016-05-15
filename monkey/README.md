# CS181 - Machine Learning (Spring 2016)

## Practical 4: Reinforcement Learning



**Team BridgingtheGAK:**

Gioia Dominedo  |  40966234 |  dominedo@g.harvard.edu

Amy Lee  |  60984077 |  amymaelee@g.harvard.edu

Kendrick Lo  |  70984997  |  klo@g.harvard.edu



**Instructions:**

This zip file includes all relevant files for our Practical 4 submission.

- Write-up: `report.pdf`
- Q-learning agent: `qlearning_agent.py`
- TD-value learning agent: `tdlearning_agent.py`
- Original Swingy Monkey game code: `SwingyMonkey.py`



To run the agents, simply run `python qlearning_agent.py` or `python tdlearning_agent.py` from the terminal. The agents are both set up to run 100 epochs with their respective "best" parameters. These parameters can be changed at the initialization step in the ``__main__`` function, i.e. by changing the line  `agent = Learner(alpha=0.01, gamma=0.7, epsilon=0.0)`. Similarly, the number of epochs can be altered through the `iters` variable in the line `score = run_games(agent, hist, iters=100, t_len=0)`. 
