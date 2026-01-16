def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr
data = [64, 34, 25, 12, 22, 11, 90]
print("До сортировки:", data)
sorted_data = insertion_sort(data.copy())
print("После сортировки:", sorted_data)
