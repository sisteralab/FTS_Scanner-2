import sys
import pyqtgraph.examples
import random
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# fig = Figure(figsize=(5, 4), dpi=150)
# ax = fig.add_subplot(111)
xdata = list(range(50))
ydata = [random.randint(0, 10) for i in range(50)]
# fig.plot(xdata,ydata)
# fig.show()
plt.plot(xdata, ydata)
plt.show()
# pyqtgraph.examples.run()
