# AVL
# Реализовать класс AVL, который будет представлять собой avl-дерево. Поддержать следующие операции:
#
# * вставка
# * удаление
# * поиск
#
# Тесты продолжаем писать.

class AVLNode:
    def __init__(self, key):
        if key is None:
            raise TypeError("Key cannot be None")
        self.key = key
        self.left = None
        self.right = None
        self.height = 1

class AVL:
    def __init__(self):
        self.root = None

    def get_height(self, node):
        if not node:
            return 0
        return node.height

    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    def update_height(self, node):
        if node:
            node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))

    def left_rotate(self, z):
        y = z.right
        T2 = y.left

        y.left = z
        z.right = T2

        self.update_height(z)
        self.update_height(y)
        return y

    def right_rotate(self, z):
        y = z.left
        T3 = y.right

        y.right = z
        z.left = T3

        self.update_height(z)
        self.update_height(y)
        return y

    def balance_node(self, node):
        balance = self.get_balance(node)

        if balance > 1 and self.get_balance(node.left) >= 0:
            return self.right_rotate(node)

        if balance < -1 and self.get_balance(node.right) <= 0:
            return self.left_rotate(node)

        if balance > 1 and self.get_balance(node.left) < 0:
            node.left = self.left_rotate(node.left)
            return self.right_rotate(node)

        if balance < -1 and self.get_balance(node.right) > 0:
            node.right = self.right_rotate(node.right)
            return self.left_rotate(node)
        return node

    def insert(self, key):
        self.root = self.insert_rec(self.root, key)

    def insert_rec(self, node, key):
        if not node:
            return AVLNode(key)

        if key < node.key:
            node.left = self.insert_rec(node.left, key)
        elif key > node.key:
            node.right = self.insert_rec(node.right, key)
        else:
            return node

        self.update_height(node)
        return self.balance_node(node)

    def find_min(self, node):
        current = node
        while current.left:
            current = current.left
        return current

    def delete(self, key):
        self.root = self.delete_rec(self.root, key)

    def delete_rec(self, node, key):
        if not node:
            return node

        if key < node.key:
            node.left = self.delete_rec(node.left, key)
        elif key > node.key:
            node.right = self.delete_rec(node.right, key)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left
            else:
                temp = self.find_min(node.right)
                node.key = temp.key
                node.right = self.delete_rec(node.right, temp.key)

        if not node:
            return node

        self.update_height(node)
        return self.balance_node(node)

    def search(self, key):
        return self.search_rec(self.root, key)

    def search_rec(self, node, key):
        if not node:
            return False

        if key == node.key:
            return True
        elif key < node.key:
            return self.search_rec(node.left, key)
        else:
            return self.search_rec(node.right, key)