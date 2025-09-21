from functions import max_even_sum

import pytest

def test_check_palindrome():
    assert max_even_sum([]) == 0
    assert max_even_sum([-1, 3, 4, 1]) == 8
    assert max_even_sum([5, 7, 13, 2, 14]) == 36
    assert max_even_sum([3]) == 0


    with pytest.raises(TypeError):
        max_even_sum(['1','1','1'])
    with pytest.raises(TypeError):
        max_even_sum()

test_check_palindrome()