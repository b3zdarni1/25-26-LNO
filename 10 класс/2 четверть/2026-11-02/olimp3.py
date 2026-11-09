import math
a = int(input())
p = []
for i in range(a):
    x, y = map(int, input().split())
    p.append((x, y))
s = 0
b = 0
for i in range(a):
    x1, y1 = p[i]
    x2, y2 = p[(i + 1) % a]
    s += x1 * y2 - x2 * y1
    b += math.gcd(abs(x1 - x2), abs(y1 - y2))
s = abs(s) / 2
r = s + b / 2 + 2
print(int(r))