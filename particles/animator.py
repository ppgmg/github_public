import matplotlib.pyplot as plt
from matplotlib.collections import EllipseCollection
import numpy as np

def randcolor():
    return np.random.uniform(0.0, 0.89, (3,)) + 0.1

class Animator(object):
    def __init__(self, positions, diameter):
        self.count = positions.shape[0]

        plt.ion()
        fig = plt.figure(figsize=(10, 10))
        ax = fig.gca()
        self.ax = ax

        diameters = np.ones(self.count) * diameter
        colors = [randcolor() for _ in range(self.count)]
        self.circles = EllipseCollection(widths=diameters,
                                         heights=diameters,
                                         angles=np.zeros_like(diameters),
                                         units='xy',
                                         offsets=positions,
                                         transOffset=ax.transData,
                                         edgecolor='face', facecolor=colors)
        ax.add_collection(self.circles)

        ax.axis([0, 1, 0, 1])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_axis_bgcolor('black')
        plt.draw()

    def update(self, positions):
        self.circles.set_offsets(positions)
        plt.draw()
