from functions import max_even_sum

if __name__ == '__main__':
    try:
        array = list(map(int, input('Введите числа: ').split()))
        max_sum = max_even_sum(array)
        print(max_sum)
    except Exception as e:
        print(e)