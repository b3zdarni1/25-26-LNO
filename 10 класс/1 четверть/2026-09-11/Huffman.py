freq = {'A': 10, 'E': 8, 'C': 6, 'B': 4, 'D': 4}

nodes = []
for letter, w in freq.items():
    nodes.append([w, letter, None, None])

while len(nodes) > 1:
    nodes.sort()
    a = nodes.pop(0)
    b = nodes.pop(0)
    new = [a[0] + b[0], '', a, b]
    nodes.append(new)

root = nodes[0]

lengths = {}
stack = [(root, 0)]

while stack:
    node, depth = stack.pop()
    if node[1] != '':
        lengths[node[1]] = depth
    else:
        stack.append((node[2], depth + 1))
        stack.append((node[3], depth + 1))


order = ['A', 'E', 'C', 'B', 'D']


items = []
for i, letter in enumerate(order):
    items.append((lengths[letter], i, letter))
items.sort()

codes = {}
code = 0
prev_len = 0

for length, _, letter in items:
    if prev_len == 0:
        code = 0
    else:
        code = (code + 1) * (2 ** (length - prev_len))

    binary = bin(code)[2:]
    binary = '0' * (length - len(binary)) + binary
    codes[letter] = binary
    prev_len = length

for letter in order:
    print(letter, '->', codes[letter])