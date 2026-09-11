count = 0
while True:
    x = int(input())
    if x == 0:
        break
    if 1 <= x <= 9 and x % 3 == 0:
        count += 1
print(count)