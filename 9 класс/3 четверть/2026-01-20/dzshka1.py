numbers = []
for i in range(10):
    num = int(input(f"Введите число {i+1}: "))
    numbers.append(num)
total = sum(numbers)
is_ascending = all(numbers[i] < numbers[i+1] for i in range(len(numbers)-1))
print(f"Сумма: {total}")
print(f"Введены в порядке возрастания: {'Да' if is_ascending else 'Нет'}")
