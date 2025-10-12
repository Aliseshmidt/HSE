from main import anagrams
import pytest


def test_anagrams():
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    result = anagrams(strs)
    expected = [["bat"], ["nat","tan"], ["ate","eat","tea"]]
    assert result == expected

    strs = ["eat", "tea", "ate"]
    result = anagrams(strs)
    expected = [["ate", "eat", "tea"]]
    assert result == expected

    strs = ["abc", "def", "ghi"]
    result = anagrams(strs)
    expected = [["abc"], ["def"], ["ghi"]]
    assert result == expected

    strs = []
    result = anagrams(strs)
    expected = []
    assert result == expected

    strs = ["hello"]
    result = anagrams(strs)
    expected = [["hello"]]
    assert result == expected

    strs = ["eat", "eat", "tea", "tea"]
    result = anagrams(strs)
    expected = [["eat", "eat", "tea", "tea"]]
    assert result == expected


def test_anagram_invalid_input():
    with pytest.raises(TypeError):
        anagrams([1, 2, 3])

    with pytest.raises(TypeError):
        anagrams(["abc", None, "def"])