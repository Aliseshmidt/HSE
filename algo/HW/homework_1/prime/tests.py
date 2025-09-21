from functions import count_prime_numbers

import pytest

def test_check_palindrome():
    assert count_prime_numbers(2) == 0
    assert count_prime_numbers(11) == 4
    assert count_prime_numbers(-131) == 0
    assert count_prime_numbers(31) == 10


    with pytest.raises(TypeError):
        count_prime_numbers('11')
    with pytest.raises(TypeError):
        count_prime_numbers()

test_check_palindrome()