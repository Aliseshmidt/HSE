import time
import random
from main import makeheap_n_log_n, makeheap

nums = [5000, 50000, 100000]

for num in nums:
    arr = [random.randint(0, 100000) for _ in range(num)]

    arr1 = arr.copy()
    start = time.time()
    print(f'\nПроверка скорости для {num} элементов:')
    makeheap_n_log_n(arr1)
    end = time.time()
    print(f'\t\tФункция n_log_n отработала за {(end-start):.4f}')

    arr2 = arr.copy()
    start = time.time()
    makeheap(arr2)
    end = time.time()
    print(f'\t\tФункция n отработала за {(end-start):.4f}')