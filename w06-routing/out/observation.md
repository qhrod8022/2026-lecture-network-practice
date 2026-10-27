# Week 6 observations

## Task 1 — Link State by Hand

Dijkstra's algorithm computes the shortest path from the source router to every reachable router based on link costs. The forwarding table stores the next-hop neighbor rather than the entire path. When multiple paths have equal costs, a consistent neighbor ordering makes the result deterministic.

## Task 2 — Break a Real Network and Time the Repair

Traceroute reveals the sequence of network hops toward a destination, although some routers may not respond to probe packets. The `* * *` output can occur when routers filter probes or rate-limit ICMP responses. OSPF reconvergence depends on failure detection timers and the time needed to calculate and distribute updated routes.

## Task 3 — Reconverge Without Recomputing the World

Avoiding unnecessary SPF recomputation can reduce redundant work when a link change does not affect the current shortest paths. The optimization requires tracking relevant topology and path information, adding memory overhead. Changes that affect shortest paths still require appropriate recomputation to preserve routing correctness.
