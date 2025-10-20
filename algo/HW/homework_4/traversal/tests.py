from main import BST

def test_bst():
    bst = BST()
    values = [4, 2, 6, 1, 3, 5, 7]
    for v in values:
        bst.insert(v)

    assert bst.pre_order() == [4, 2, 1, 3, 6, 5, 7]
    assert bst.post_order() == [1, 3, 2, 5, 7, 6, 4]
    assert bst.in_order() == [1, 2, 3, 4, 5, 6, 7]
    assert bst.reverse_pre_order() == [4, 6, 7, 5, 2, 3, 1]
    assert bst.reverse_post_order() == [7, 5, 6, 3, 1, 2, 4]
    assert bst.reverse_in_order() == [7, 6, 5, 4, 3, 2, 1]

    bst_empty = BST()
    assert bst_empty.pre_order() == []
    assert bst_empty.post_order() == []
    assert bst_empty.in_order() == []
    assert bst_empty.reverse_pre_order() == []
    assert bst_empty.reverse_post_order() == []
    assert bst_empty.reverse_in_order() == []

    bst_single = BST()
    bst_single.insert(42)
    assert bst_single.pre_order() == [42]
    assert bst_single.post_order() == [42]
    assert bst_single.in_order() == [42]
    assert bst_single.reverse_pre_order() == [42]
    assert bst_single.reverse_post_order() == [42]
    assert bst_single.reverse_in_order() == [42]

    bst_wrong_type = BST()
    try:
        bst_wrong_type.insert(None)
        assert False, "Ошибка при вставке None"
    except TypeError:
        pass

    bst_wrong_type.insert(5)
    try:
        bst_wrong_type.insert("string")
        assert False, "Ошибка при смешивании несовместимых типов"
    except TypeError:
        pass