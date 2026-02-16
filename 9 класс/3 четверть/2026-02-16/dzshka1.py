import turtle as t
t.speed(0)
t.hideturtle()
for i in range(10000):
    if ((i & -i) << 1 & i) != 0:
        t.left(90)
    else:
        t.right(90)
    t.forward(3)
t.done()
