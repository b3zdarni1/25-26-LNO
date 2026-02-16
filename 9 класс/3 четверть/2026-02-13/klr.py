import turtle as t
t.speed(0)
com = "FLFRRFLF"
rast = 2
a = 60
b = 60
q = int(input())
for u in range(3):
    for c in com:
        if c == "F":
            t.forward(rast)
        elif c == "R":
            t.right(a)
        elif c == "L":
            t.left(a)
    for i in range(q):
        for j in com:
            if j == "F" :
                com = com.replace("F", "FLFRRFLF")
    t.right(120)
t.done()
