# K-th
# Найти k-ый по величине элемент массива.
# Важно: нельзя просто отсортировать массив. Также не используем кучи, так как про них еще пока не знаем.
# Подсказка: quickselect.
#
# Ввод: nums = [3,2,1,5,6,4], k = 2
# Вывод: 5
#
# Ввод: nums = [3,2,3,1,2,4,5,5,6], k = 4
# Вывод: 4

import random


def find_kth(nums, k):
    def quick_select(arr, k_i):
        if len(arr) == 1:
            return arr[0]

        pivot = arr[int((len(arr)-1)/2)]

        left = [x for x in arr if x > pivot]
        equel = [x for x in arr if x == pivot]
        right = [x for x in arr if x < pivot]

        if k_i < len(left):
            return quick_select(left, k_i)
        elif k_i < len(left) + len(equel):
            return pivot
        else:
            return quick_select(right, k_i - len(left) - len(equel))
        
    return quick_select(nums, k - 1)