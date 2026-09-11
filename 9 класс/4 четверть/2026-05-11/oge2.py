n = int(input())
z = None
for i in range(n):
    x = int(input())
    if x % 2 == 0:
        if z is None or x < z:
            z = x
print(z)