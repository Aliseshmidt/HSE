from main import find_kth, find_kth_heapq
import random


def test_find_kth():
    nums = [3, 2, 1, 5, 6, 4]
    k = 2
    res = find_kth(nums, k)
    assert res == 5

    nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]
    k = 4
    res = find_kth(nums, k)
    assert res == 4

    nums = [1]
    k = 1
    res = find_kth(nums, k)
    assert res == 1

    nums = [1, 2, 3, 4, 5]
    k = 1
    res = find_kth(nums, k)
    assert res == 5

    nums = [1, 2, 3, 4, 5]
    k = 5
    res = find_kth(nums, k)
    assert res == 1

    nums = [5, 5, 5, 5, 5]
    k = 3
    res = find_kth(nums, k)
    assert res == 5

    for _ in range(20):
        n = random.randint(5, 50)
        k = random.randint(1, n)
        nums = [random.randint(-100, 100) for _ in range(n)]

        sorted_nums = sorted(nums, reverse=True)
        exp = sorted_nums[k - 1]

        res = find_kth(nums, k)
        assert res == exp


def test_find_kth_heapq():
    nums = [3, 2, 1, 5, 6, 4]
    k = 2
    res = find_kth_heapq(nums, k)
    assert res == 5

    nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]
    k = 4
    res = find_kth_heapq(nums, k)
    assert res == 4

    nums = [1]
    k = 1
    res = find_kth_heapq(nums, k)
    assert res == 1

    nums = [1, 2, 3, 4, 5]
    k = 1
    res = find_kth_heapq(nums, k)
    assert res == 5

    nums = [1, 2, 3, 4, 5]
    k = 5
    res = find_kth_heapq(nums, k)
    assert res == 1

    nums = [5, 5, 5, 5, 5]
    k = 3
    res = find_kth_heapq(nums, k)
    assert res == 5

    nums = [-1, -3, -2, -5, -4]
    k = 2
    res = find_kth_heapq(nums, k)
    assert res == -2

    for _ in range(20):
        n = random.randint(5, 50)
        k = random.randint(1, n)
        nums = [random.randint(-100, 100) for _ in range(n)]

        sorted_nums = sorted(nums, reverse=True)
        exp = sorted_nums[k - 1]

        res = find_kth_heapq(nums, k)
        assert res == exp