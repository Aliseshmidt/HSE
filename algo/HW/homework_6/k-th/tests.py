from main import find_kth
import random


def test_find_kth():
    nums = [3, 2, 1, 5, 6, 4]
    k = 2
    result = find_kth(nums, k)
    assert result == 5

    nums = [3, 2, 3, 1, 2, 4, 5, 5, 6]
    k = 4
    result = find_kth(nums, k)
    assert result == 4

    nums = [1, 2, 3, 4, 5]
    k = 1
    result = find_kth(nums, k)
    assert result == 5

    nums = [10, 20, 30, 40, 50]
    k = 5
    result = find_kth(nums, k)
    assert result == 10

    nums = [7, 7, 7, 7, 7]
    k = 3
    result = find_kth(nums, k)
    assert result == 7