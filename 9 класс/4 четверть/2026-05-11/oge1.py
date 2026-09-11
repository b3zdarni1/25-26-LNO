n = int(input())
count = 0
for i in range(n):
    x = int(input())
    if x % 10 == 9:
        count += 1
print(count)