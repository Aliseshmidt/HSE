from main import lcs
import random
import string

def test_lcs():
    s1 = "AGGTAB"
    s2 = "GXTXAYB"
    res = lcs(s1, s2)
    assert res == "GTAB"

    s1 = "ABCBDAB"
    s2 = "BDCABA"
    res = lcs(s1, s2)
    assert len(res) == 4


def test_lcs_single():
    assert lcs("", "") == ""
    assert lcs("abc", "") == ""
    assert lcs("", "abc") == ""

    assert lcs("a", "a") == "a"
    assert lcs("a", "b") == ""


def test_lcs_single_char():
    s1 = "aaaa"
    s2 = "aa"
    res = lcs(s1, s2)
    assert res == "aa"

    s1 = "abcde"
    s2 = "c"
    res = lcs(s1, s2)
    assert res == "c"


def is_subseq(sub, s):
    it = iter(s)
    return all(c in it for c in sub)


def test_lcs_random():
    for i in range(20):
        n = random.randint(5, 15)
        m = random.randint(5, 15)

        s1 = "".join(random.choice(string.ascii_lowercase) for i in range(n))
        s2 = "".join(random.choice(string.ascii_lowercase) for i in range(m))

        res = lcs(s1, s2)

        assert is_subseq(res, s1)
        assert is_subseq(res, s2)
