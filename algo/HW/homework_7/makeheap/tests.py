from main import makeheap_n_log_n, makeheap
import pytest
import random

def is_min(arr):
    n = len(arr)
    for i in range(n):
        left = 2*i + 1
        right = 2*i + 2
        if left < n and arr[i] > arr[left]:
            return False
        if right < n and arr[i] > arr[right]:
            return False
    return True

def test_makeheap_n_log_n():
    arr = [10, 5, 7, 16, 13, 2, 20]
    makeheap_n_log_n(arr)
    assert is_min(arr) == True

    for _ in range(20):
        arr = [random.randint(-1000, 1000) for _ in range(50)]
        makeheap_n_log_n(arr)
        assert is_min(arr)

    arr = []
    makeheap_n_log_n(arr)
    assert arr == []

    arr = [42]
    makeheap_n_log_n(arr)
    assert arr == [42]

    arr = [1, 3, 5, 7, 9, 11]
    makeheap_n_log_n(arr)
    assert is_min(arr)


def test_makeheap():
    arr = [10, 5, 7, 16, 13, 2, 20]
    makeheap(arr)
    assert is_min(arr) == True

    for _ in range(20):
        arr = [random.randint(-1000, 1000) for _ in range(50)]
        makeheap(arr)
        assert is_min(arr)

    arr = []
    makeheap(arr)
    assert arr == []

    arr = [42]
    makeheap(arr)
    assert arr == [42]

    arr = [1, 3, 5, 7, 9, 11]
    makeheap(arr)
    assert is_min(arr)

