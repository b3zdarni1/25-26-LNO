with open('values.txt', 'r') as f:
    d = f.read().split()
with open('packed.bin', 'wb') as f:
    f.write(bytes([int(x) for x in d]))