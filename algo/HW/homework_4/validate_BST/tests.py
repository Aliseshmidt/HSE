from main import TreeNode, check_in_order


def test_valid_bst():
    root = TreeNode(3)
    root.left = TreeNode(2)
    root.right = TreeNode(5)
    root.left.left = TreeNode(1)
    root.left.right = TreeNode(3)
    root.right.right = TreeNode(6)

    assert check_in_order(root) == True
    assert check_in_order(None) == True

    root = TreeNode(1)
    assert check_in_order(root) == True

    root = TreeNode(-2)
    root.left = TreeNode(-3)
    root.right = TreeNode(-1)
    root.left.left = TreeNode(-4)
    root.right.right = TreeNode(0)
    assert check_in_order(root) == True

    root = TreeNode(1)
    root.right = TreeNode(2)
    root.right.right = TreeNode(3)
    root.right.right.right = TreeNode(4)
    assert check_in_order(root) == True

    root = TreeNode(3.3)
    root.left = TreeNode(2.2)
    root.right = TreeNode(4.4)
    root.left.left = TreeNode(1.1)
    root.right.left = TreeNode(3.3)
    root.right.right = TreeNode(5.5)
    assert check_in_order(root) == True


def test_invalid_bst():
    root = TreeNode(3)
    root.left = TreeNode(2)
    root.right = TreeNode(2)
    assert check_in_order(root) == False

    root = TreeNode(4)
    root.left = TreeNode(2)
    root.right = TreeNode(5)
    root.left.left = TreeNode(1)
    root.left.right = TreeNode(5)
    assert check_in_order(root) == False

    root = TreeNode(3)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    assert check_in_order(root) == False

    root = TreeNode(3)
    root.left = TreeNode(3)
    assert check_in_order(root) == False

    root = TreeNode(-2)
    root.left = TreeNode(-1)
    root.right = TreeNode(-3)
    assert check_in_order(root) == False

    root = TreeNode(3)
    root.right = TreeNode(2)
    root.right.right = TreeNode(1)
    root.right.right.right = TreeNode(0)
    assert check_in_order(root) == False

    root = TreeNode(3.3)
    root.left = TreeNode(2.2)
    root.right = TreeNode(3.3)
    assert check_in_order(root) == False