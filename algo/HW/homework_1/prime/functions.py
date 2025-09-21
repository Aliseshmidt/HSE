# Временная сложность - О(n**2)
# Пространственная сложность - О(1)

def check_prime(num: int) -> bool:
    if num < 2:
        return False
    for i in range(2, num-1):
        if num % i == 0:
            return False
    return True

def count_prime_numbers(num: int) -> int:
    count = 0

    for i in range(num):
        if check_prime(i):
            count += 1

    return count

