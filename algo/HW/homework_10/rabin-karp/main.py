# Rabin-Karp
# Реализовать поиск подстроки в строке с помощью алгоритма Рабина-Карпа. 
# 
# К решению нужно прикрепить отчет с
# 
# * объяснением rolling hash
# * оценкой сложности итогового алгоритма
# 
# Тесты продолжаем писать.

def char_value(c):
    return ord(c) - ord('a') + 1


def rabin_karp(text, sub_str):
    n = len(text)
    m = len(sub_str)

    if m == 0 or m > n:
        return []

    p = 17
    mod = 10**10+7
    pol = 1
    for i in range(m - 1):
        pol = (pol * p) % mod

    sub_str_hash = 0
    for c in sub_str:
        sub_str_hash = ((sub_str_hash * p) + char_value(c)) % mod

    curr_hash = 0
    for i in range(m):
        curr_hash = ((curr_hash * p) + char_value(text[i])) % mod

    result = []

    for i in range(n - m + 1):
        if curr_hash == sub_str_hash:
            if text[i:i + m] == sub_str:
                result.append(i)
        if i < (n - m):
            left = char_value(text[i])
            right = char_value(text[i + m])
            curr_hash = ((curr_hash - (left * pol)) * p + right) % mod
            if curr_hash < 0:
                curr_hash += mod

    return result

# text = "ababcabcab"
# sub_str = "abc"
#
# print(rabin_karp(text, sub_str))
