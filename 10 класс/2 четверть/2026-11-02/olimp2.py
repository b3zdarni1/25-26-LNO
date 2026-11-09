a = input()
b = input()
c = ''
for i in range(5):
    if a[i].isupper():
        c += a[i]
    else:
        c += b[i]
print(c.upper())