slovo = input()
def ver(slovo):
    otr = {}
    for i in slovo:
        c = 0
        for j in slovo:
            if i == j:
                c = c + 1
        otr[i] = c/len(slovo)
    return otr
print(ver(slovo))
def sep(slovo):
    o = [0]
    for i in ver(slovo):
        prev = ver(slovo)[i]
        if o[-1] + prev <= 1:
            o.append(o[-1] + prev)
        else:
            break
    return o
def alg(slovo):
    sep = globals()['sep'](slovo)
    L = 0
    R = 1
    v = ver(slovo)
    keys = list(v.keys())
    for a in slovo:
        idx = keys.index(a)
        old_L = L
        old_R = R
        L = old_L + sep[idx] * (old_R - old_L)
        R = old_L + sep[idx + 1] * (old_R - old_L)
    return L, R
print(alg(slovo))