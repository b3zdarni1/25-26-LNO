nums = input().split()
def utf(x):
    answ = []
    if x <= 2**7 - 1:
        answ = [x]
    elif x <= 2**11 - 1:
        answ = [
            0b11000000 | (x >> 6),
            0b10000000 | (x & 0b111111)
        ]
    elif x <= 2**15 - 1:
        answ = [
            0b11100000 | (x >> 12),
            0b10000000 | ((x >> 6) & 0b111111),
            0b10000000 | (x & 0b111111)
        ]
    else:
        answ = [
            0b11110000 | (x >> 18),
            0b10000000 | ((x >> 12) & 0b111111),
            0b10000000 | ((x >> 6) & 0b111111),
            0b10000000 | (x & 0b111111)
        ]
    return " ".join(f"{b:08b}" for b in answ)
with open('nums.txt', 'w') as f:
    for num in nums:
        f.write(utf(int(num)) + "\n")