a = int(input())
def space(a,b,w,h):
    return a*b - w*h
b = []
for i in range(a):
    ai = int(input())
    bi = int(input())
    wi = int(input())
    hi = int(input())
    b.append(space(ai,bi,wi,hi))
    b[i] = space(ai,bi,wi,hi)
c = sorted(b)
for i in range(a):
    for j in range(a):
        if c[i] == b[j]:
            c[i] = j+1
print(c)