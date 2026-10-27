#!/usr/bin/env python3
"""Week 6 · Task 3 — avoid unnecessary full SPF runs after link changes."""
import heapq

SPF_RUNS = 0


def dijkstra_table(graph, source):
    """Reference SPF. Every full table rebuild passes through this counter."""
    global SPF_RUNS
    SPF_RUNS += 1
    best = {source: (0, None)}
    pq, done = [(0, source, None)], set()
    while pq:
        cost, node, first_hop = heapq.heappop(pq)
        if node in done:
            continue
        done.add(node)
        best[node] = (cost, first_hop)
        for nbr, weight in sorted(graph[node].items()):
            if nbr in done:
                continue
            hop = nbr if node == source else first_hop
            if cost + weight < best.get(nbr, (float("inf"), None))[0]:
                best[nbr] = (cost + weight, hop)
                heapq.heappush(pq, (cost + weight, nbr, hop))
    return {dest: hop for dest, (_, hop) in best.items() if dest != source and hop}


def _distances(graph, source):
    """Maintain distance metadata used to decide whether a link event matters."""
    dist = {source: 0}
    queue = [(0, source)]
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != dist.get(node):
            continue
        for nbr, weight in graph[node].items():
            candidate = cost + weight
            if candidate < dist.get(nbr, float("inf")):
                dist[nbr] = candidate
                heapq.heappush(queue, (candidate, nbr))
    return dist


class FullRecompute:
    """Baseline: recompute the complete table after every event."""
    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = dijkstra_table(self.graph, source)

    def link_change(self, a, b, cost):
        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost
        self.table = dijkstra_table(self.graph, self.source)


class YourRouter:
    """Keep distances and skip SPF when an event cannot change shortest routes.

    A failure or cost increase requires SPF only when the old link lay on a
    shortest route. A link addition or cost decrease requires SPF only when it
    can improve (or tie and alter) a shortest distance. Distance metadata is
    refreshed only after an actual SPF recomputation.
    """
    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = dijkstra_table(self.graph, source)
        self.dist = _distances(self.graph, source)

    def link_change(self, a, b, cost):
        old = self.graph[a].get(b)
        if cost is None and old is None:
            return
        if cost is not None and old == cost:
            return

        da = self.dist.get(a, float("inf"))
        db = self.dist.get(b, float("inf"))
        if old is None:
            affected = (cost is not None and
                        (da + cost <= db or db + cost <= da))
        elif cost is None or cost > old:
            affected = (da + old == db or db + old == da)
        else:  # cost decreased
            affected = (da + cost <= db or db + cost <= da)

        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost

        if affected:
            self.table = dijkstra_table(self.graph, self.source)
            self.dist = _distances(self.graph, self.source)
