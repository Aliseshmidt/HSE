from main import kmp_search
import random
import string


def test_kmp():
    text = "ababcabcab"
    sub_str = "abc"
    res = kmp_search(text, sub_str)
    assert res == [2, 5]

    text = "aaaaa"
    sub_str = "aa"
    res = kmp_search(text, sub_str)
    assert res == [0, 1, 2, 3]

    text = "abcdef"
    sub_str = "def"
    res = kmp_search(text, sub_str)
    assert res == [3]

    text = "abcdef"
    sub_str = "xyz"
    res = kmp_search(text, sub_str)
    assert res == []


def test_kmp_single():
    text = ""
    sub_str = "a"
    res = kmp_search(text, sub_str)
    assert res == []

    text = "a"
    sub_str = ""
    res = kmp_search(text, sub_str)
    assert res == []

    text = "short"
    sub_str = "longerpattern"
    res = kmp_search(text, sub_str)
    assert res == []


def test_kmp_single_char():
    text = "aaaaa"
    sub_str = "a"
    res = kmp_search(text, sub_str)
    assert res == [0, 1, 2, 3, 4]

    text = "abcde"
    sub_str = "c"
    res = kmp_search(text, sub_str)
    assert res == [2]


def test_kmp_random():
    for i in range(20):
        n = random.randint(10, 100)
        m = random.randint(1, 5)

        text = "".join(random.choice(string.ascii_lowercase) for i in range(n))
        sub_str = "".join(random.choice(string.ascii_lowercase) for i in range(m))

        expected = []
        for i in range(len(text) - len(sub_str) + 1):
            if text[i:i + len(sub_str)] == sub_str:
                expected.append(i)

        res = kmp_search(text, sub_str)
        assert res == expected
