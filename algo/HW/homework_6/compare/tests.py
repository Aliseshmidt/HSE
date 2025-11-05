from main import quicksort, mergesort
import random

def test_correct():
    test_data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    expected = sorted(test_data)

    quick_result = quicksort(test_data)[0]
    merge_result = mergesort(test_data)[0]

    assert quick_result == expected
    assert merge_result == expected
    assert quick_result == merge_result


def test_time():
    data = [random.randint(-100, 100) for _ in range(100)]
    quick_time = quicksort(data)[1]
    merge_time = mergesort(data)[1]
    assert quick_time < merge_time

    data = [random.randint(-10000, 10000) for _ in range(10000)]
    quick_time = quicksort(data)[1]
    merge_time = mergesort(data)[1]
    assert quick_time < merge_time

    data = list(range(1000))
    quick_time = quicksort(data)[1]
    merge_time = mergesort(data)[1]
    assert quick_time < merge_time

    data = list(range(999, -1, -1))
    quick_time = quicksort(data)[1]
    merge_time = mergesort(data)[1]
    assert quick_time < merge_time

    data = [random.choice([1, 2, 3]) for _ in range(1000)]
    quick_time = quicksort(data)[1]
    merge_time = mergesort(data)[1]
    assert quick_time < merge_time