# DAG
# Дан ориентированный граф.
#
# 1) Нужно определить, есть ли в графе цикл
# 2) Если цикл есть -- вывести его (достаточно одного цикла)
# 3) Если цикла нет -- применяем топологическую сортировку и выводим результат
#
# Подразумевается, что граф подается на вход в виде списка смежности (словарь со списками ребер).
#
# Тесты.

def dag(graph: dict):
    visited = set()
    stack = set()
    parent = {}
    cycle_arr = []

    def dfs(node):
        visited.add(node)
        stack.add(node)
        for neigh in graph.get(node, []):
            if neigh not in visited:
                parent[neigh] = node
                if dfs(neigh):
                    return True
            elif neigh in stack:
                cycle = [neigh]
                cur = node
                while cur != neigh:
                    cycle.append(cur)
                    cur = parent[cur]
                cycle.append(neigh)
                cycle.reverse()
                cycle_arr.extend(cycle)
                return True
        stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True, cycle_arr

    start_points = {u: 0 for u in graph}

    for u in graph:
        for v in graph[u]:
            start_points[v] = start_points.get(v, 0) + 1

    queue = [u for u in graph if start_points[u] == 0]
    topo = []

    while queue:
        u = queue.pop()
        topo.append(u)
        for v in graph.get(u, []):
            start_points[v] -= 1
            if start_points[v] == 0:
                queue.append(v)

    return False, topo