n = int(input())
k = int(input())
s = int(input())
if k <= s or(n < k and k <= n+s):
    print("0")
elif s != 0:
     print(min(abs(k - s),abs(k - (n+s)),abs(k - (n+1))))
else:
    print(k-1)