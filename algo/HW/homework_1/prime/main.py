from functions import count_prime_numbers


if __name__ == '__main__':
    try:
        num = int(input('Введите число: '))
        print(f'Кол-во простых чисел < {num}: {count_prime_numbers(num)}')
    except Exception as e:
        print(e)