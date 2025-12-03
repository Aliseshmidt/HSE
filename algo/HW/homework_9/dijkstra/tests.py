from main import dijkstra

def test_empty():
    assert dijkstra({}, 'A') == {}

def test_single_node():
    graph = {'A': []}
    assert dijkstra(graph, 'A') == {'A': 0}

def test_two_nodes():
    graph = {
        'A': [('B', 5)],
        'B': []
    }
    assert dijkstra(graph, 'A') == {'A': 0, 'B': 5}

def test_ordinary():
    graph = {
        'A': [('B', 1), ('C', 4)],
        'B': [('C', 2)],
        'C': []
    }
    result = dijkstra(graph, 'A')
    expected = {'A': 0, 'B': 1, 'C': 3}
    assert result == expected

    graph = {
        'A': [('B', 4), ('C', 2)],
        'B': [('C', 1), ('D', 5)],
        'C': [('D', 8), ('E', 10)],
        'D': [('E', 2)],
        'E': []
    }
    result = dijkstra(graph, 'A')
    expected = {'A': 0, 'B': 4, 'C': 2, 'D': 9, 'E': 11}
    assert result == expected

    graph = {
        'A': [('B', 3)],
        'B': [('A', 2), ('C', 4)],
        'C': [('B', 1)]
    }
    
    result = dijkstra(graph, 'B')
    expected = {'B': 0, 'A': 2, 'C': 4}
    assert result == expected

def test_separate_nodes():
    graph = {
        'A': [('B', 3)],
        'B': [],
        'C': [('D', 1)],
        'D': []
    }
    result = dijkstra(graph, 'A')
    assert result['A'] == 0
    assert result['B'] == 3
    assert result['C'] == float('inf')
    assert result['D'] == float('inf')

