# Даны 2 последовательности pushed и popped, содержащие уникальные целые числа.
# popped  является перестановкой pushed, то есть, все элементы совпадают,
# но может отличаться порядок.
#
# Программа должна вернуть True, если эти последовательности могут
# получиться в результате некоторой последовательности операций push и pop на пустом стеке.

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


def validate(pushed: list, popped: list) -> bool:
    if len(pushed) != len(popped):
        return False
    stack = Stack()
    j = 0

    for el in pushed:
        stack.push(el)
        while stack and j < len(popped) and stack.peek() == popped[j]:
            stack.pop()
            j += 1

    return j == len(popped)

# Временная сложность - О(n)
# Пространственная сложность - О(n)