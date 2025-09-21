from functions import check_palindrome


if __name__ == '__main__':
    try:
        num = int(input('Введите число для проверки палиндрома: '))
        if check_palindrome(num):
            print('Число - палиндром')
        else:
            print('Число не является палиндромом')
    except Exception as e:
        print(e)