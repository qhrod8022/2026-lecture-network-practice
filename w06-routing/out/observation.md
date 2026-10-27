# Week 6 observations

## Task 1 — Link state by hand
Dijkstra gives the minimum cost from the source to every reachable router; the forwarding table stores only the first-hop neighbour, not the complete path. Equal-cost choices are deterministic: neighbours are visited in sorted order and a route is replaced only when its cost is strictly lower.

## Task 2 — Break a real network and time the repair
**Complete this section with measurements from your own machine before submitting.** `traceroute.txt`, `route-before.txt`, `route-after.txt`, and `reconverge.txt` must contain actual command output; they have not been fabricated here. Record the domestic exit hop, the likely ocean-crossing hop/cable, the hop count to 1.1.1.1, and two reasons for `* * *` (no reply/filtered or rate-limited probes; and a hop/router that does not return TTL-expired responses).

For the OSPF portion, record the measured down and restore times and compare them with the hello/dead intervals in `topology/r1/frr.conf`. A failure can take longer because the router may have to wait for neighbour-dead detection; restoration can be faster because Hellos can establish the neighbour again and trigger new LSAs. A cost change does not wait for failure detection, so it is usually faster.

## Task 3 — Reconverge without recomputing the world
The router keeps shortest distances between events and skips a full SPF when a changed link cannot improve a route or is not on a shortest route. This metadata uses O(V) extra memory; actual affected events still require a complete SPF to guarantee correctness. Python wall time may be slower because the checks and metadata maintenance add overhead, but avoiding repeated SPF work is valuable on routers where CPU and large topology calculations are the scarce resources.
