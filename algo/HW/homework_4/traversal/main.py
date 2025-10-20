# Traversal
# Реализовать все обходы дерева:
#
# pre-order~~
# post-order~~
# in-order~~
# reverse pre-order~~
# reverse post-order~~
# reverse in-order~~
#
# Важно!
# Решение сопроводить тестами
# Класс BST реализуем самостоятельно
# В классе BST необходимо поддержать вставку для удобства тестирования

class BSTNode:
    def __init__(self, key):
        if key is None:
            raise TypeError("Key cannot be None")
        self.key = key
        self.left = None
        self.right = None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, key):
        if self.root is None:
            self.root = BSTNode(key)
        else:
            self.insert_rec(self.root, key)

    def insert_rec(self, node, key):
        if key < node.key:
            if node.left is None:
                node.left = BSTNode(key)
            else:
                self.insert_rec(node.left, key)
        else:
            if node.right is None:
                node.right = BSTNode(key)
            else:
                self.insert_rec(node.right, key)

    def pre_order(self):
        result = []
        self.pre_order_rec(self.root, result)
        return result

    def pre_order_rec(self, node, result):
        if node is not None:
            result.append(node.key)
            self.pre_order_rec(node.left, result)
            self.pre_order_rec(node.right, result)

    def post_order(self):
        result = []
        self.post_order_rec(self.root, result)
        return result

    def post_order_rec(self, node, result):
        if node is not None:
            self.post_order_rec(node.left, result)
            self.post_order_rec(node.right, result)
            result.append(node.key)

    def in_order(self):
        result = []
        self.in_order_rec(self.root, result)
        return result

    def in_order_rec(self, node, result):
        if node is not None:
            self.in_order_rec(node.left, result)
            result.append(node.key)
            self.in_order_rec(node.right, result)

    def reverse_pre_order(self):
        result = []
        self.reverse_pre_order_rec(self.root, result)
        return result

    def reverse_pre_order_rec(self, node, result):
        if node is not None:
            result.append(node.key)
            self.reverse_pre_order_rec(node.right, result)
            self.reverse_pre_order_rec(node.left, result)

    def reverse_post_order(self):
        result = []
        self.reverse_post_order_rec(self.root, result)
        return result

    def reverse_post_order_rec(self, node, result):
        if node is not None:
            self.reverse_post_order_rec(node.right, result)
            self.reverse_post_order_rec(node.left, result)
            result.append(node.key)

    def reverse_in_order(self):
        result = []
        self.reverse_in_order_rec(self.root, result)
        return result

    def reverse_in_order_rec(self, node, result):
        if node is not None:
            self.reverse_in_order_rec(node.right, result)
            result.append(node.key)
            self.reverse_in_order_rec(node.left, result)