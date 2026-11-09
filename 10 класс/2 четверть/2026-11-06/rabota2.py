with open('numbers.txt', 'r') as f:
    numbers_str = f.read().split()
total = sum(int(num) for num in numbers_str)
with open('sum.txt', 'w') as f:
    f.write(str(total))