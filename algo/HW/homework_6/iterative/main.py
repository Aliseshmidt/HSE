# Iterative
# Реализовать итеративные версии mergesort и quicksort.
#
# Тесты продолжаем писать.

import time
import random
from collections import deque


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} выполнена за {end - start:.6f} секунд")
        return (res, end-start)
    return wrapper

@timer
def quicksort(arr):
    if len(arr) <= 1:
        return arr

    stack = deque()
    stack.append((0, len(arr) - 1))
    arr = arr.copy()

    while stack:
        low, high = stack.pop()
        if low >= high:
            continue
        pivot = arr[(low + high)//2]
        i = low - 1
        j = high + 1
        while True:
            i += 1
            while arr[i] < pivot:
                i += 1
            j -= 1
            while arr[j] > pivot:
                j -= 1
            if i >= j:
                break
            arr[i], arr[j] = arr[j], arr[i]

        stack.append((low, j))
        stack.append((j + 1, high))
    return arr

def merge_arrays(arr1, arr2):
    arr = []
    n_arr1, n_arr2 = len(arr1), len(arr2)

    i,j = 0,0
    while i<n_arr1 and j<n_arr2:
        if arr1[i] <= arr2[j]:
            arr.append(arr1[i])
            i+=1
        else:
            arr.append(arr2[j])
            j+=1
    arr += arr1[i:] + arr2[j:]
    return arr

@timer
def mergesort(arr):
    stack = [[i] for i in arr]
    while len(stack) > 1:
        new_stack = []
        for i in range(0, len(stack), 2):
            if i + 1 < len(stack):
                new_stack.append(merge_arrays(stack[i], stack[i + 1]))
            else:
                new_stack.append(stack[i])
        stack = new_stack
    return stack[0] if stack else []


small_arr = [random.randint(-10, 10) for _ in range(10)]
large_arr = [random.randint(-10000, 10000) for _ in range(10000)]
sorted_arr = list(range(1000))
reversed_arr = sorted_arr[::-1]

print("Маленький массив:")
print(quicksort(small_arr.copy()))
print(mergesort(small_arr.copy()))

print("\nБольшой массив:")
quicksort(large_arr.copy())
mergesort(large_arr.copy())

print("\nОтсортированный массив:")
quicksort(sorted_arr.copy())
mergesort(sorted_arr.copy())

print("\nОбратно отсортированный массив:")
quicksort(reversed_arr.copy())
mergesort(reversed_arr.copy())