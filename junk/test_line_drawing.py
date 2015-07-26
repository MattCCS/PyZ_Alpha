
from mpl_toolkits.mplot3d import Axes3D # IMPORTANT
import matplotlib.pyplot as plt

import line_drawing
import line_drawing_2

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

import numpy as np
s = np.array([[50, -37]])
S = line_drawing_2.bresenhamline(s, np.zeros(s.shape[1]), max_iter=-1)
# S = line_drawing_2.get_line((0,0), (10,20))
print S
ax.scatter(*zip(*S), c='r', marker='o')

plt.show()