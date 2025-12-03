from main import dag

def test_empty():
    assert dag({}) == (False, [])

def test_no_cycle():
    g = {"A":["B"], "B":["C"], "C":[]}
    has_cycle, out = dag(g)
    assert not has_cycle
    assert out == ["A","B","C"]

def test_ordinary():
    g = {"A":["B"], "B":["A"]}
    has_cycle, cycle = dag(g)
    assert has_cycle
    assert len(cycle) >= 3

    g = {"A": ["B"], "B": ["C"], "C": ["A"], "D": []}
    has_cycle, cycle = dag(g)
    assert has_cycle
    assert set(cycle).issubset({"A", "B", "C"})

    g = {1: [2], 2: [], 3: [2], 4: []}
    has_cycle, topo = dag(g)
    assert not has_cycle
    assert set(topo) == {1, 2, 3, 4}

