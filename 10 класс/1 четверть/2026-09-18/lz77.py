tokens = [
    (0,0,'a'),
    (0,0,'b'),
    (2,1,'d'),
    (2,1,'k'),
    (4,3,'b'),
    (0,0,'r'),
    (3,1,None),
    ]
def decode(tokens):
    result = []
    for offset, length, char in tokens:
        i = 0
        while i < length:
            result.append(result[len(result) - offset])
            i = i + 1
        if char != None:
            result.append(char)
    return result
print(decode(tokens))