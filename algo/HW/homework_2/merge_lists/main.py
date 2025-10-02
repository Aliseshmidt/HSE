# Даны два отсортированных односвязных списка list1 и list2
#
# Необходимо объединить их в один новый отсортированный список.
# Новый список должен быть составлен слиянием узлов двух исходных списков.
# Вернуть необходимо голову объединенного списка.
#
# Вход: list1 = [1,2,4], list2 = [1,3,4]
# Выход: [1,1,2,3,4,4]
#
# Требования:
# * реализовать два способа решения поставленной задачи: с использованием фиктивного элемента и без него
# * написать тесты

class Node:
    def __init__(self, value):
        self.next = None
        self.value = value



def merge_two_lists_with_node(list1: Node, list2: Node) -> Node:
    head = result = Node(None)

    while list1 or list2:
        if list1 is None:
            result.next = Node(list2.value)
            list2 = list2.next
        elif list2 is None:
            result.next = Node(list1.value)
            list1 = list1.next
        elif list1.value < list2.value:
            new_node = Node(list1.value)
            result.next = new_node
            list1 = list1.next
        else:
            new_node = Node(list2.value)
            result.next = new_node
            list2 = list2.next
        result = result.next

    head = head.next

    return head

def merge_two_lists_wo_node(list1: Node, list2: Node) -> Node:
    if list1 is None:
        return list2
    if list2 is None:
        return list1

    if list1.value < list2.value:
        head = list1
        list1 = list1.next
    else:
        head = list2
        list2 = list2.next

    curr = head

    while list1 or list2:
        if list1 is None:
            curr.next = list2
            list2 = list2.next
        elif list2 is None:
            curr.next = list1
            list1 = list1.next
        elif list1.value < list2.value:
            curr.next = list1
            list1 = list1.next
        else:
            curr.next = list2
            list2 = list2.next
        curr = curr.next

    return head


# Временная сложность - О(n+m)
# Пространственная сложность - О(n+m)