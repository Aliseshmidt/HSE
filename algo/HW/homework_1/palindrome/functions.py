# Временная сложность - О(log10n) где n - число
# Пространственная сложность - О(1)

def num_reverse(num: int) -> int:
    reversed = 0
    num_orig = abs(num)

    while num_orig // 10 != 0:
        reversed = reversed*10 + num_orig%10
        num_orig = num_orig//10

    reversed = reversed*10 + num_orig%10
    return reversed

def check_palindrome(num: int) -> bool:
    num_reversed = num_reverse(num)
    if num_reversed == num and type(num) == int and type(num_reversed) == int:
        return True
    else:
        return False


