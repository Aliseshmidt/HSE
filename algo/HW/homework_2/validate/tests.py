import pytest
from main import validate, Stack


def test_validate():
    pushed = [1, 2, 3, 4, 5]
    popped = [1, 3, 5, 4, 2]
    assert validate(pushed, popped) == True

    pushed = [1, 2, 3]
    popped = [3, 1, 2]
    assert validate(pushed, popped) == False

    pushed = [1, 2, 3, 4, 5]
    popped = [1, 2, 3, 4, 5]
    assert validate(pushed, popped) == True

    pushed = [1, 2, 3, 4, 5]
    popped = [5, 4, 3, 2, 1]
    assert validate(pushed, popped) == True

    pushed = [1, 2, 3, 4, 5]
    popped = [4, 5, 3, 2, 1]
    assert validate(pushed, popped) == True

    pushed = [1, 2, 3, 4, 5]
    popped = [4, 3, 5, 1, 2]
    assert validate(pushed, popped) == False


def test_validate_empty():
    pushed = []
    popped = []
    assert validate(pushed, popped) == True


def test_validate_single():
    pushed = [1]
    popped = [1]
    assert validate(pushed, popped) == True

    pushed = [1]
    popped = [2]
    assert validate(pushed, popped) == False


def test_validate_different_len():
    pushed = [1, 2, 3]
    popped = [1, 2]
    assert validate(pushed, popped) == False

    pushed = [1, 2]
    popped = [1, 2, 3]
    assert validate(pushed, popped) == False


def test_validate_duplicates():
    pushed = [1, 2, 2, 3, 4]
    popped = [2, 3, 2, 4, 1]
    assert validate(pushed, popped) == True

    pushed = [1, 2, 2, 3, 4]
    popped = [2, 3, 4, 2, 1]
    assert validate(pushed, popped) == True