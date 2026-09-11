N = int(input())
b = 0
all_solved = False
for i in range(N):
    solved = int(input())
    if solved < 5:
        b += 1
    if solved == 10:
        all_solved = True
print(b)
print("YES" if all_solved else "NO")