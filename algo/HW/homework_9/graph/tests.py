from main import find_components

def test_empty():
    assert find_components({}) == []

def test_single_node():
    assert find_components({"A": []}) == [["A"]]

def test_separate_nodes():
    graph = {"A": [], "B": [], "C": []}
    result = find_components(graph)
    expected = [["A"], ["B"], ["C"]]
    assert sorted([sorted(c) for c in result]) == sorted([sorted(c) for c in expected])

def test_ordinary():
    graph = {
        "A": ["B"],
        "B": ["A", "C"],
        "C": ["B"],
        "D": []
    }
    result = find_components(graph)
    res_sorted = [sorted(c) for c in result]
    assert len(res_sorted) == 2
    assert sorted(["A", "B", "C"]) in res_sorted
    assert ["D"] in res_sorted

    graph = {
        1: [2],
        2: [1],
        3: [],
        4: [5],
        5: [4]
    }
    result = find_components(graph)
    res_sorted = [sorted(c) for c in result]
    expected = [sorted([1,2]), [3], sorted([4,5])]
    assert res_sorted == expected

def test_missing_node():
    g = {"A": ["B"], "B": []}
    assert sorted([sorted(c) for c in find_components(g)]) == sorted([["A", "B"]])

    g2 = {"A": ["B"]}
    result = find_components(g2)
    assert result == [["A"]]

def test_self_loop():
    g = {"A": ["A"]}
    result = find_components(g)
    assert result == [["A"]]

def test_mixed_types():
    g = {"A": [1], 1: ["A"]}
    result = find_components(g)
    res_sorted = sorted([sorted(map(str, c)) for c in result])
    assert res_sorted == [["1", "A"]]