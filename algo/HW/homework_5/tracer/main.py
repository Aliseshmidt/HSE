# Tracer
# Реализовать декоратор, который показывает стек вызовов рекурсивных функций
#
# На каждом шаге должен быть виден:
# * вход в рекурсию (вызов функции),
# * отступ, соответствующий глубине стека,
# * возврат из рекурсии с результатом

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
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n=n-1)


@tracer
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

print("Факториал 3:")
factorial(3)

print("Числа Фибоначчи n=3:")
fib(3)