from main import AVL
import pytest


def test_avl_insert_and_search():
    avl = AVL()
    values = [10, 20, 30, 40, 50, 25]

    for v in values:
        avl.insert(v)

    assert avl.search(10) == True
    assert avl.search(20) == True
    assert avl.search(30) == True
    assert avl.search(40) == True
    assert avl.search(50) == True
    assert avl.search(25) == True

    assert avl.search(5) == False
    assert avl.search(100) == False
    assert avl.search(35) == False


def test_avl_delete():
    avl = AVL()
    values = [10, 20, 30, 40, 50, 25]

    for v in values:
        avl.insert(v)

    avl.delete(25)
    assert avl.search(25) == False
    assert avl.search(20) == True
    assert avl.search(30) == True

    avl.delete(20)
    assert avl.search(20) == False

    avl.delete(30)
    assert avl.search(30) == False

    avl.delete(10)
    assert avl.search(10) == False


def test_avl_invalid_input():
    avl = AVL()

    with pytest.raises(TypeError):
        avl.insert(None)

    avl.insert(1)
    avl.insert(2)

    assert avl.search(1) == True
    assert avl.search(2) == True