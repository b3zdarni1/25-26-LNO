a = int(input())
for i in range(a):
    c = int(input())
    d = list(map(int, input().split()))
    idx = d.index(min(d))
    d[idx] += 1
    b = 1
    for q in d:
        b *= q
    print(b)