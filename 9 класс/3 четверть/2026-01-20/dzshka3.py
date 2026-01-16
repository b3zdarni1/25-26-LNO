def matrix_multiply(A, B):
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])
    
    if cols_A != rows_B:
        raise ValueError("Умножение невозможно: число столбцов A != число строк B")
    
    result = [[0 for _ in range(cols_B)] for _ in range(rows_A)]
    
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]
    
    return result
A = [[1, 2, 3],
     [4, 5, 6]]
B = [[7, 8],
     [9, 10],
     [11, 12]]
C = matrix_multiply(A, B)
print("Результат умножения:")
for row in C:
    print(row)