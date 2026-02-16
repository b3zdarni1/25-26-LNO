import numpy as np
import math as m

def angle_mejdu(u, v):
    u = np.array(u)
    v = np.array(v)
    proiz = np.dot(u, v)
    mod_u = np.linalg.norm(u)
    mod_v = np.linalg.norm(v)
    cos_ugla = proiz / (mod_u * mod_v)
    return np.degrees(m.acos(cos_ugla))
spisok = [[1,0],[0,1],[-1,0],[0,-1]]
def ortv(spisok):
    for u in spisok:
        for v in spisok:
            if angle_mejdu(u,v) == 90 or angle_mejdu(u,v) == 270:
                print(u,v)
print(ortv(spisok))