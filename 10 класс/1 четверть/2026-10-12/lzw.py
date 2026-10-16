def LZW(text):

    dict = {}
    i = 0

    for char in text:
        if char not in dict:
            dict[char] = i
            i += 1

    res = []
    cur = ""

    for char in text:
        if cur + char in dict:
            cur += char
        else:
            dict[cur + char] = i
            res.append(dict[cur])
            i += 1
            cur = char

    if cur:
        res.append(dict[cur])

    return res, dict


print(LZW("abobaaboba"))


def LZW_decode(codes, alph):
    d = list(alph)
    out = ""
    prev = ""

    for code in codes:
        if code < len(d):
            s = d[code]
        else:
            s = prev + prev[0]

        out = out + s

        if prev != "":
            d.append(prev + s[0])

        prev = s

    return out


codes, _ = LZW("abobaaboba")
print(LZW_decode(codes, "abo"))












