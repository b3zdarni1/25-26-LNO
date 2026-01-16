def insertion_sort(arr):
    a = arr.copy()
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j+1] = a[j]
            j -= 1
        a[j+1] = key
    return a

lst = list(map(int, input("Введите числа через пробела: ").split()))
sorted_lst = insertion_sort(lst)
print("Отсортированный массив:", sorted_lst)
