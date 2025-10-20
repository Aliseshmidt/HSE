# Balanced binary tree
# Дано бинарное дерево. Определить, является ли оно сбалансированным по высоте.
#
# Сбалансированное по высоте бинарное дерево — это бинарное дерево, в котором глубина двух поддеревьев каждого узла никогда не отличается более чем на единицу.
#
# Важно!
# Тесты, в рамках которых необходимо рассмотреть как можно больше краевых кейсов.

class TreeNode:
    def __init__(self, key):
        if key is None:
            raise TypeError("Key cannot be None")
        self.key = key
        self.left = None
        self.right = None

def check_balanced(root):
    def check_height(node):
        if node is None:
            return 0

        left_h = check_height(node.left)
        if left_h == -1:
            return -1

        right_h = check_height(node.right)
        if right_h == -1:
            return -1

        if abs(left_h - right_h) > 1:
            return -1

        return max(left_h, right_h) + 1

    return check_height(root) != -1