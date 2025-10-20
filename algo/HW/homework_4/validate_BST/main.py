# Validate BST
# На вход приходит root бинарного дерева.
# Необходимо проверить, является ли это дерево бинарным деревом поиска.
#
# Важно!
# Тесты, в рамках которых необходимо рассмотреть как можно больше краевых кейсов.


# BST свойства:
# 1. Левое поддерево любого узла содержит только значения МЕНЬШЕ значения узла
# 2. Правое поддерево любого узла содержит только значения БОЛЬШЕ значения узла
# 3. Оба поддерева должны быть BST

# Можно проверить с помощью прохода in_order (вернет отсортированную последовательность)

class TreeNode:
    def __init__(self, key):
        if key is None:
            raise TypeError("Key cannot be None")
        self.key = key
        self.left = None
        self.right = None


def check_in_order(root):
    def check_in_order_rec(node, result):
        if node is not None:
            check_in_order_rec(node.left, result)
            result.append(node.key)
            check_in_order_rec(node.right, result)
    result = []
    check_in_order_rec(root, result)
    print(result, sorted(list(set(result))))
    return result == sorted(list(set(result)))