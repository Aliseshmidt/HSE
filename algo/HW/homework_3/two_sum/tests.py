from main import two_sum
import pytest


def test_two_sum():
    arr = [1, 3, 4, 10]
    k = 7
    result = two_sum(arr, k)
    expected = [1, 2]
    assert result == expected

    arr = [5, 5, 1, 4]
    k = 10
    result = two_sum(arr, k)
    expected = [0, 1]
    assert result == expected

    arr = [-1, 2, 5, 8]
    k = 7
    result = two_sum(arr, k)
    expected = [1, 2]
    assert result == expected

    arr = [0, 3, 7, 0]
    k = 0
    result = two_sum(arr, k)
    expected = [0, 3]
    assert result == expected

    arr = list(range(1000))
    k = 1997
    result = two_sum(arr, k)
    expected = [998, 999]
    assert result == expected


def test_two_sum_invalid_input():
    with pytest.raises(TypeError):
        two_sum("not_a_list", 5)

    with pytest.raises(TypeError):
        two_sum([1, 2, 3], "not_an_integer")

    with pytest.raises(TypeError):
        two_sum([1, "string", 3], 5)