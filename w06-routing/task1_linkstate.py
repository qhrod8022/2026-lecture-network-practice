#!/usr/bin/env python3
"""Week 6 · Task 1 — Link state: Dijkstra and forwarding tables."""
import argparse
import heapq

TOPOLOGY = {
    "u": {"v": 2, "w": 5, "x": 1},
    "v": {"u": 2, "w": 3, "x": 2},
    "w": {"u": 5, "v": 3, "x": 3, "y": 1, "z": 5},
    "x": {"u": 1, "v": 2, "w": 3, "y": 1},
    "y": {"w": 1, "x": 1, "z": 2},
    "z": {"w": 5, "y": 2},
}


def dijkstra(graph, source):
    """Return shortest distance from source to each reachable node."""
    if source not in graph:
        return {}
    distances = {source: 0}
    queue = [(0, source)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances.get(node):
            continue
        for neighbour, weight in sorted(graph[node].items()):
            candidate = distance + weight
            if candidate < distances.get(neighbour, float("inf")):
                distances[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    return {node: distance for node, distance in distances.items() if node != source}


def forwarding_table(graph, source):
    """Return destination -> first hop, using deterministic sorted-neighbour ties."""
    if source not in graph:
        return {}
    best = {source: (0, None)}
    queue = [(0, source, None)]
    settled = set()
    while queue:
        cost, node, first_hop = heapq.heappop(queue)
        if node in settled:
            continue
        settled.add(node)
        best[node] = (cost, first_hop)
        for neighbour, weight in sorted(graph[node].items()):
            if neighbour in settled:
                continue
            hop = neighbour if node == source else first_hop
            candidate = cost + weight
            if candidate < best.get(neighbour, (float("inf"), None))[0]:
                best[neighbour] = (candidate, hop)
                heapq.heappush(queue, (candidate, neighbour, hop))
    return {destination: hop for destination, (_, hop) in best.items()
            if destination != source and hop is not None}


def link_down(graph, a, b):
    """Return a copy of graph with undirected link a-b removed."""
    copied = {node: dict(edges) for node, edges in graph.items()}
    copied.get(a, {}).pop(b, None)
    copied.get(b, {}).pop(a, None)
    return copied


EXPECTED_COST_U = {"v": 2, "w": 3, "x": 1, "y": 2, "z": 4}
EXPECTED_TABLE_U = {"v": "v", "w": "x", "x": "x", "y": "x", "z": "x"}


def verify():
    fails = 0
    cost = dijkstra(TOPOLOGY, "u")
    ok = cost == EXPECTED_COST_U
    print(f"  {'ok  ' if ok else 'FAIL'}  costs from u: {cost}")
    if not ok:
        print(f"        expected {EXPECTED_COST_U}")
    fails += not ok
    table = forwarding_table(TOPOLOGY, "u")
    ok = table == EXPECTED_TABLE_U
    print(f"  {'ok  ' if ok else 'FAIL'}  table at u:  {table}")
    if not ok:
        print(f"        expected {EXPECTED_TABLE_U}")
    fails += not ok
    for node in TOPOLOGY:
        table = forwarding_table(TOPOLOGY, node)
        missing = set(TOPOLOGY) - {node} - set(table)
        bad = [dest for dest, hop in table.items() if hop not in TOPOLOGY[node]]
        ok = not missing and not bad
        print(f"  {'ok  ' if ok else 'FAIL'}  table at {node} covers all, hops are neighbours"
              + (f"  missing={missing} bad={bad}" if not ok else ""))
        fails += not ok
    cut = link_down(TOPOLOGY, "u", "x")
    after = forwarding_table(cut, "u")
    ok = after != EXPECTED_TABLE_U
    print(f"  {'ok  ' if ok else 'FAIL'}  u reroutes when u-x goes down: {after}")
    fails += not ok
    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    raise SystemExit(verify() if args.verify else parser.print_help())
