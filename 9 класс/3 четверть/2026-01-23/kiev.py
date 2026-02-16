import turtle
t = turtle.Turtle()
t.shape("turtle")
t.color("blue")
t.speed(100)
'''def spiral(a,b):
    i = b*2
    q = a*i
    t.teleport(-q / 2, q / 2)
    for i in range (1,i):
        for w in range(1,3):
            t.forward(q)
            t.right(90)
        q -= a
spiral(10,10)

turtle.done()'''
'''def snegr(n,k):
    t.right(180)
    t.circle(10)
    g = 10 * n
    for i in range(0,k):
        t.circle(g)
        t.left(90)
        t.penup()
        t.forward(2*g)
        t.pendown()
        t.right(90)
        g =g * 10
snegr(10,10)
turtle.done()'''
t.fillcolor('red')
t.begin_fill()
t.left(180)
t.forward(375)
t.left(90)
t.forward(325)
t.left(90)
t.forward(750)
t.left(90)
t.forward(325)
t.left(90)
t.forward(375)
t.end_fill()
turtle.done()