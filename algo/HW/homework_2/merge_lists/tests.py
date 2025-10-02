from main import merge_two_lists_with_node, merge_two_lists_wo_node, Node
import pytest


def test_merge_two_lists_with_node():
    list1 = Node(1)
    list1.next = Node(2)
    list1.next.next = Node(4)

    list2 = Node(1)
    list2.next = Node(3)
    list2.next.next = Node(4)
    list2.next.next.next = Node(5)
    list2.next.next.next.next = Node(6)

    result = merge_two_lists_with_node(list1, list2)
    expected = [1, 1, 2, 3, 4, 4, 5, 6]

    current = result
    for val in expected:
        assert current.value == val
        current = current.next
    assert current is None

    list1 = None
    list2 = Node(1)
    list2.next = Node(2)

    result = merge_two_lists_with_node(list1, list2)
    expected = [1, 2]

    current = result
    for val in expected:
        assert current.value == val
        current = current.next
    assert current is None

    list1 = None
    list2 = None

    result = merge_two_lists_with_node(list1, list2)
    assert result is None


def test_merge_two_lists_wo_node():
    list1 = Node(1)
    list1.next = Node(2)
    list1.next.next = Node(4)

    list2 = Node(1)
    list2.next = Node(3)
    list2.next.next = Node(4)
    list2.next.next.next = Node(5)
    list2.next.next.next.next = Node(6)

    result = merge_two_lists_wo_node(list1, list2)
    expected = [1, 1, 2, 3, 4, 4, 5, 6]

    current = result
    for val in expected:
        assert current.value == val
        current = current.next
    assert current is None

    list1 = None
    list2 = Node(1)
    list2.next = Node(2)

    result = merge_two_lists_wo_node(list1, list2)
    expected = [1, 2]

    current = result
    for val in expected:
        assert current.value == val
        current = current.next
    assert current is None

    list1 = None
    list2 = None

    result = merge_two_lists_wo_node(list1, list2)
    assert result is None

    list1 = Node(1)
    list1.next = Node(5)
    list1.next.next = Node(10)

    list2 = Node(2)
    list2.next = Node(3)

    result = merge_two_lists_wo_node(list1, list2)
    expected = [1, 2, 3, 5, 10]

    current = result
    for val in expected:
        assert current.value == val
        current = current.next
    assert current is None



def test_invalid_input():
    with pytest.raises(AttributeError):
        merge_two_lists_with_node("not_a_list", Node(1))

    with pytest.raises(AttributeError):
        merge_two_lists_wo_node(Node(1), "not_a_list")