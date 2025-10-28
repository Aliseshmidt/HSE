from main import permute
import pytest


def test_permute_valid():
    nums = [1, 2, 3]
    res = permute(nums)
    expected = [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    assert len(res) == len(expected)
    for p in expected:
        assert p in res

    nums = [0, 1]
    res = permute(nums)
    expected = [[0, 1], [1, 0]]

    assert len(res) == len(expected)
    for p in expected:
        assert p in res

    nums = [1]
    res = permute(nums)
    expected = [[1]]
    assert res == expected

    nums = []
    res = permute(nums)
    expected = [[]]
    assert res == expected

    nums = [1, 1]
    res = permute(nums)
    expected = [[1, 1], [1, 1]]
    assert len(res) == len(expected)
    for p in expected:
        assert p in res

    nums = [-1, -2]
    res = permute(nums)
    expected = [[-1, -2], [-2, -1]]
    assert len(res) == len(expected)
    for p in expected:
        assert p in res