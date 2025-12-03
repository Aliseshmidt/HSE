# Graph
# Дан неориентированный граф.
# Необходимо, найти все компоненты связности графа и вывести их.
# Подразумевается, что граф подается на вход в виде списка смежности (словарь со списками ребер).
# Здесь очень важны краевые случаи. Тесты должны их покрыть.

from collections import deque

def find_components(graph: dict) -> list:
    visited = set()
    components = []

    for node in graph:
        if node not in visited:
            comp = []
            queue = deque([node])
            visited.add(node)
            while queue:
                cur = queue.popleft()
                comp.append(cur)
                neighbors = graph.get(cur) or []
                for neigh in neighbors:
                    if neigh in graph and neigh not in visited:
                        visited.add(neigh)
                        queue.append(neigh)
            components.append(comp)

    return components
