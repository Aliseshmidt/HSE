# LCS
# Longest common subsequence
#
# Даны две строки.
# Найти самую длинную последовательность символов, которая встречается в заданном порядке в обеих строках. Символы не обязательно должны идти подряд
# string_1 = "AGGTAB"
# string_2 = "GXTXAYB"
# LCS = "GTAB"
# Тесты.

def lcs(s1, s2):
    n = len(s1)
    m = len(s2)

    if n == 0 or m == 0:
        return ""

    dp = [[0] * (m + 1) for i in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    i, j = n, m
    res = []

    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            res.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    return "".join(reversed(res))
