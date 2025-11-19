# K-th minheap
# Найти k-ый по величине элемент массива. Важно: нельзя просто отсортировать массив. Для решения необходимо использовать minheap.
# На выходе должно быть две реализции:
#
# 1) без использования heapq (кучу и методы работы с ней реализовываем сами)
# 2) с использованием heapq
#
# Ввод: nums = [3,2,1,5,6,4], k = 2
# Вывод: 5
#
# Ввод: nums = [3,2,3,1,2,4,5,5,6], k = 4
# Вывод: 4

import heapq

def sift_down(heap, i, n):
    while (2*i + 1) < n:
        left = 2*i + 1
        right = 2*i + 2
        low = left
        if right < n and heap[right] < heap[left]:
            low = right
        if heap[i] <= heap[low]:
            break
        heap[i], heap[low] = heap[low], heap[i]
        i = low


def makeheap(arr):
    n = len(arr)
    for i in range(n//2-1, -1, -1):
        sift_down(arr, i, n)

def find_kth(nums, k):
    n = len(nums)

    heap = nums[:k].copy()
    makeheap(heap)

    for i in range(k, n):
        if nums[i] > heap[0]:
            heap[0] = nums[i]
            sift_down(heap, 0, k)

    return heap[0]


def find_kth_heapq(nums, k):
    heap = nums[:k]
    heapq.heapify(heap)

    for i in range(k, len(nums)):
        if nums[i] > heap[0]:
            heapq.heappop(heap)
            heapq.heappush(heap, nums[i])

    return heap[0]

