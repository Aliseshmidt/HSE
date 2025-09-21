from functions import check_palindrome

import pytest

def test_check_palindrome():
    assert check_palindrome(2) == True
    assert check_palindrome(11) == True
    assert check_palindrome(-131) == False
    assert check_palindrome(31) == False
    assert check_palindrome(33333333333) == True


    with pytest.raises(TypeError):
        check_palindrome('11')
    with pytest.raises(TypeError):
        check_palindrome()

test_check_palindrome()