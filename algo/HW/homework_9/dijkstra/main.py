# Dijkstra's
# Реализовать алгоритм Дейкстры для взвешенного графа.
# Тесты.

import heapq

def dijkstra(graph: dict, start):
    if not graph or start not in graph:
        return {}

    distances = {node: float('inf') for node in graph}
    distances[start] = 0

    queue_dist = [(0, start)]

    while queue_dist:
        curr_dist, node = heapq.heappop(queue_dist)

        if curr_dist > distances[node]:
            continue

        for neighbor, weight in graph.get(node, []):
            new_dist = curr_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(queue_dist, (new_dist, neighbor))

    return distances

