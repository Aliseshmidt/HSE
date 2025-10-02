import pytest
from main import Stack, Queue, Node


def test_stack_init():
    stack = Stack()
    assert stack.top is None


def test_stack_push():
    stack = Stack()
    stack.push(1)
    assert stack.top.value == 1
    assert stack.top.next is None

    stack.push(2)
    assert stack.top.value == 2
    assert stack.top.next.value == 1


def test_stack_pop():
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)

    assert stack.pop() == 3
    assert stack.pop() == 2
    assert stack.pop() == 1
    assert stack.pop() is None


def test_stack_peek():
    stack = Stack()
    assert stack.peek() is None

    stack.push(1)
    assert stack.peek() == 1

    stack.push(2)
    assert stack.peek() == 2

    stack.pop()
    assert stack.peek() == 1


def test_stack_lifo():
    stack = Stack()
    values = [1, 2, 3, 4, 5]

    for value in values:
        stack.push(value)

    for value in reversed(values):
        assert stack.pop() == value


def test_stack_empty():
    stack = Stack()
    assert stack.pop() is None
    assert stack.peek() is None


def test_queue_init():
    queue = Queue()
    assert queue.first is None
    assert queue.last is None


def test_queue_enqueue():
    queue = Queue()
    queue.enqueue(1)
    assert queue.first.value == 1
    assert queue.last.value == 1
    assert queue.first is queue.last

    queue.enqueue(2)
    assert queue.first.value == 1
    assert queue.last.value == 2
    assert queue.last.next is None


def test_queue_dequeue():
    queue = Queue()
    queue.enqueue(1)
    queue.enqueue(2)
    queue.enqueue(3)

    assert queue.dequeue() == 1
    assert queue.dequeue() == 2
    assert queue.dequeue() == 3
    assert queue.dequeue() is None
    assert queue.first is None
    assert queue.last is None


def test_queue_peek():
    queue = Queue()
    assert queue.peek() is None

    queue.enqueue(1)
    assert queue.peek() == 1

    queue.enqueue(2)
    assert queue.peek() == 1

    queue.dequeue()
    assert queue.peek() == 2


def test_queue_fifo():
    queue = Queue()
    values = [1, 2, 3, 4, 5]

    for value in values:
        queue.enqueue(value)

    for value in values:
        assert queue.dequeue() == value


def test_queue_empty():
    queue = Queue()
    assert queue.dequeue() is None
    assert queue.peek() is None


def test_stack_types():
    stack = Stack()

    test_data = [1, "hello", 3.14, [1, 2, 3], {"key": "value"}]

    for item in test_data:
        stack.push(item)

    for item in reversed(test_data):
        assert stack.pop() == item


def test_queue_types():
    queue = Queue()

    test_data = [1, "hello", 3.14, [1, 2, 3], {"key": "value"}]

    for item in test_data:
        queue.enqueue(item)

    for item in test_data:
        assert queue.dequeue() == item
