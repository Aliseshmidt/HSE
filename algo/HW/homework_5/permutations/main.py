# Permutations
# На вход дан массив. Необходимо вернуть все возможные перестановки.
#
# Вход: nums = [1,2,3]
# Выход: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
# Вход: nums = [0,1]
# Выход: [[0,1],[1,0]]
# Вход: nums = [1]
# Выход: [[1]]
# Обязательно: в реализации предусмотреть визуализацию стека вызовов, в идеале использовать декоратор из первой задачи.
#
# Тесты продолжаем писать.

import functools


def tracer(func):
    lvl = 0

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal lvl
        tab = "   " * lvl
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v}" for k, v in kwargs.items()]
        params = ", ".join(args_repr + kwargs_repr)
        print(f"{tab}-> {func.__name__}({params})")
        lvl += 1
        try:
            res = func(*args, **kwargs)
        finally:
            lvl -= 1
        print(f"{tab}<- {func.__name__} returns {res}")
        return res

    return wrapper


@tracer
def permute(nums):
    if len(nums) == 0:
        return [[]]
    result = []
    for i in range(len(nums)):
        n = nums[i]
        part = nums[:i] + nums[i + 1:]
        for p in permute(part):
            result.append([n] + p)
    return result