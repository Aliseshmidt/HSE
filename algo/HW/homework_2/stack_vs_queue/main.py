# Stack vs queue
# Реализовать стек и очередь на основе связных списков. Без использования сторонних библиотек.
#
# Требования:
# * Напишите тесты, которые проверяют реализацию.
# * Реализовать тесты можно любым способом (unittest, pytest)

class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class Stack:
    def __init__(self):
        self.top = None

    def push(self, value):
        new_node = Node(value)
        new_node.next = self.top
        self.top = new_node

    def pop(self):
        if self.top is None:
            return None
        value = self.top.value
        self.top = self.top.next
        return value

    def peek(self):
        if self.top is None:
            return None
        value = self.top.value
        return value


class Queue:
    def __init__(self):
        self.first = None
        self.last = None

    def enqueue(self, value):
        new_node = Node(value)
        if self.last is None:
            self.first = new_node
            self.last = self.first
        else:
            self.last.next = new_node
            self.last = new_node

    def dequeue(self):
        if self.first is None:
            return None
        value = self.first.value
        self.first = self.first.next
        if self.first is None:
            self.last = None
        return value

    def peek(self):
        if self.first is None:
            return None
        value = self.first.value
        return value
