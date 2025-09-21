# Временная сложность - О(n)
# Пространственная сложность - О(1)

def max_even_sum(arr:list[int]) -> int:
    list_sum = sum(arr)
    if list_sum % 2 != 0:
        list_sum -= min([x for x in arr if x%2!=0])
    return list_sum


