# Knuth–Morris–Pratt
# Реализовать поиск подстроки в строке с помощью алгоритма Кнута — Морриса — Пратта 
# 
# К решению нужно прикрепить отчет с
# 
# * объяснением алгоритма
# * оценкой сложности итогового алгоритма
# 
# Тесты продолжаем писать.

def get_arr_pref(sub_str):
    m = len(sub_str)
    arr_pref = [0] * m

    l = 0
    i = 1

    while i < m:
        if sub_str[i] == sub_str[l]:
            l += 1
            arr_pref[i] = l
            i += 1
        else:
            if l != 0:
                l = arr_pref[l - 1]
            else:
                arr_pref[i] = 0
                i += 1

    return arr_pref


def kmp_search(text, sub_str):
    n = len(text)
    m = len(sub_str)

    if m == 0 or m > n:
        return []

    arr_pref = get_arr_pref(sub_str)

    result = []
    i = 0
    j = 0

    while i < n:
        if text[i] == sub_str[j]:
            i += 1
            j += 1

        if j == m:
            result.append(i - j)
            j = arr_pref[j - 1]

        elif i < n and text[i] != sub_str[j]:
            if j != 0:
                j = arr_pref[j - 1]
            else:
                i += 1

    return result
