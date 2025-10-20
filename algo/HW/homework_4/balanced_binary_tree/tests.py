from main import TreeNode, check_balanced

def test_balanced_true():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)
    root.right.left = TreeNode(6)
    root.right.right = TreeNode(7)

    assert check_balanced(root) == True
    assert check_balanced(None) == True

    root = TreeNode(1)
    assert check_balanced(root) == True

    root = TreeNode(1)
    root.left = TreeNode(2)
    assert check_balanced(root) == True

    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    assert check_balanced(root) == True

    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.right = TreeNode(4)

    assert check_balanced(root) == True

def test_balanced_false():
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.left.left = TreeNode(3)
    assert check_balanced(root) == False

    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)
    root.right.left = TreeNode(6)
    root.left.left.left = TreeNode(7)
    assert check_balanced(root) == True

    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.right.right = TreeNode(5)
    root.right.right.right = TreeNode(6)
    root.right.right.right.right = TreeNode(7)
    assert check_balanced(root) == False
