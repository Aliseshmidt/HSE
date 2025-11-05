# Compare
#
# Реализовать рекурсивные версии mergesort и quicksort.
# Реализовать декоратор, который будет замерять время выполнения функции.
# Придумать тесты, на которых время выполнения этих методов будет прилично отличаться.

import time
import random


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} выполнена за {end - start:.6f} секунд")
        return (result, end-start)
    return wrapper

def _quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[int((len(arr)-1)/2)]
    left = []
    right = []
    equal = []
    for num in arr:
        if num < pivot:
            left.append(num)
        elif num == pivot:
            equal.append(num)
        elif num>pivot:
            right.append(num)
    return _quicksort(left) + equal + _quicksort(right)

@timer
def quicksort(arr):
    return _quicksort(arr)


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

def _mergesort(arr):
    pivot = len(arr)//2
    left = arr[:pivot]
    right = arr[pivot:]

    if len(left) > 1:
        left = _mergesort(left)
    if len(right) > 1:
        right = _mergesort(right)

    return merge_arrays(left, right)


@timer
def mergesort(arr):
    return _mergesort(arr)


small_arr = [random.randint(-100, 100) for _ in range(100)]
large_arr = [random.randint(-10000, 10000) for _ in range(10000)]
sorted_arr = list(range(1000))
reversed_arr = sorted_arr[::-1]

print("Маленький массив:")
quicksort(small_arr.copy())
mergesort(small_arr.copy())

print("\nБольшой массив:")
quicksort(large_arr.copy())
mergesort(large_arr.copy())

print("\nОтсортированный массив:")
quicksort(sorted_arr.copy())
mergesort(sorted_arr.copy())

print("\nОбратно отсортированный массив:")
quicksort(reversed_arr.copy())
mergesort(reversed_arr.copy())