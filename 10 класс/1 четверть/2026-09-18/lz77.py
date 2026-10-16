a = int(input())
b = []
for i in range(a):
    b.append((input()))
for i in b:
    if i == 'bca' or i == 'cab':
        print('NO')
    else:
        print('YES')