import numpy as np
import matplotlib.pyplot as plt
x = np.array([0, 1, 2, 3, 4])
y = np.array([0, 1, 4, 9, 16])
n = len(x)
def l1(i, xx):
    result = 1
    for j in range(n):
        if (j==i):
            continue
        result *= (xx-x[j]) / (x[i] - x[j])
    return result
def L(x):
    result = 0
    for i in range(n):
        result += y[i]*l1(i,x)
    return result

xxx = np.linspace(0, 4, 100)
plt.plot(xxx, L(xxx))

plt.show()