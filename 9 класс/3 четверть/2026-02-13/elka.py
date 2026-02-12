import turtle as t
t.shape("turtle")
t.color("green")
t.hideturtle()
'''brc это branches count короче количество веточек
brdist это branches distance шаг между ветками
brst это branches step шаг арифметич прогрессии
'''
def elka(brc,brdist,brst):
    t.speed(300)
    angle = 45
    stvol = 50
    fdlin = 15
    t.teleport(0,stvol + brdist*(brc - 1))
    for i in range(brc):
        t.setheading(270)
        t.left(angle)
        t.forward(fdlin)
        t.right(180)
        t.forward(fdlin)
        t.left(90)
        t.forward(fdlin)
        t.right(180)
        t.forward(fdlin)
        t.right(180 - angle)
        t.forward(brdist)
        fdlin += brst
    t.forward(stvol)
elka(6,30,15)
t.done()
