# Makeheap
# 1) Реализуйте функцию makeheap_n_log_n(arr), которая преобразует произвольный массив arr в minheap за O(N log N).
# 2) Реализуйте функцию makeheap(arr), которая преобразует произвольный массив arr в minheap за O(N).
# К решению необходимо прикрепить отчет/фото, в котором будет объяснен подход и доказана сложность (подсказка: необходимо аккуратно выписать сумму).
# Важно! Нельзя использовать встроенные библиотеки.
# В финале -- сравните время работы двух методов.
#
# Итог, на выходе этой задачи:
# - две функции makeheap_n_log_n(arr), makeheap(arr)
# - файл с доказательством асимптотической сложности для makeheap
# - тесты
# - сравнение времени выполнения двух методов (в любом виде)


def sift_up(heap, i):
    while i > 0:
        parent = (i-1)//2
        if heap[parent] <= heap[i]:
            break
        heap[parent], heap[i] = heap[i], heap[parent]
        i = parent

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

def makeheap_n_log_n(arr):
    n = len(arr)
    for i in range(1, n):
        sift_up(arr, i)

def makeheap(arr):
    n = len(arr)
    for i in range(n//2-1, -1, -1):
        sift_down(arr, i, n)
