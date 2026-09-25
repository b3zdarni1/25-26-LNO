t = int(input())
for _ in range(t):
    score = 0
    for i in range(10):
        row = input().strip()
        for j in range(10):
            if row[j] == 'X':
                score += min(i, j, 9 - i, 9 - j) + 1
    print(score)