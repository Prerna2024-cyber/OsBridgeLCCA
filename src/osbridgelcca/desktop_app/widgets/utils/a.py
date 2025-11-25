i=0.00515
r=0.0067
a=sum(((1 + i) / (1 + r)) ** period for period in range(1, 50, 1))
print(a)