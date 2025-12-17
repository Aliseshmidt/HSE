from main import rabin_karp
import random
import string

def test_rabin_karp():
    text = "ababcabcab"
    sub_str = "abc"
    res = rabin_karp(text, sub_str)
    assert res == [2, 5]

    text = "aaaaa"
    sub_str = "aa"
    res = rabin_karp(text, sub_str)
    assert res == [0, 1, 2, 3]

    text = "abcdef"
    sub_str = "def"
    res = rabin_karp(text, sub_str)
    assert res == [3]

    text = "abcdef"
    sub_str = "xyz"
    res = rabin_karp(text, sub_str)
    assert res == []


def test_rabin_karp_single():
    text = ""
    sub_str = "a"
    res = rabin_karp(text, sub_str)
    assert res == []

    text = "a"
    sub_str = ""
    res = rabin_karp(text, sub_str)
    assert res == []

    text = "a"
    sub_str = "a"
    res = rabin_karp(text, sub_str)
    assert res == [0]

    text = "short"
    sub_str = "longersub_str"
    res = rabin_karp(text, sub_str)
    assert res == []


def test_rabin_karp_single_char():
    text = "aaaaa"
    sub_str = "a"
    res = rabin_karp(text, sub_str)
    assert res == [0, 1, 2, 3, 4]

    text = "abcde"
    sub_str = "c"
    res = rabin_karp(text, sub_str)
    assert res == [2]


def test_rabin_karp_random():
    for i in range(20):
        n = random.randint(10, 100)
        m = random.randint(1, 5)

        text = "".join(random.choice(string.ascii_lowercase) for i in range(n))
        sub_str = "".join(random.choice(string.ascii_lowercase) for i in range(m))

        # эталонный результат
        expected = []
        for i in range(len(text) - len(sub_str) + 1):
            if text[i:i + len(sub_str)] == sub_str:
                expected.append(i)

        res = rabin_karp(text, sub_str)
        assert res == expected
