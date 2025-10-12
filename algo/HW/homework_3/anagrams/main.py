# Дан список слов. Сгруппируйте слова так, чтобы в одной группе оказались все анаграммы.
#
# Требования:
#
# * тесты

# Input: strs = ["eat","tea","tan","ate","nat","bat"]
# Output: [["bat"],["nat","tan"],["ate","eat","tea"]]

print(sorted(tuple('teaa')), tuple('eat'))
def anagrams(strs: list) -> list:
    dict_strs = {}
    for s in strs:
        curr = tuple(sorted(s))
        if curr in dict_strs.keys():
            dict_strs[curr].append(s)
        else:
            dict_strs[curr] = [s]
    sorted_groups = [sorted(group) for group in dict_strs.values()]
    return sorted(sorted_groups, key=len)

print(anagrams(["eat","tea","tan","ate","nat","bat"]))

# Временная сложность - О(n**2)
# Пространственная сложность - О(n)
