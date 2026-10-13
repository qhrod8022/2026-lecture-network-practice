# Week 4 observations

**Task 1:** I used stop-and-wait ARQ because it makes it straightforward to accept only the expected sequence number and retransmit after a timeout. The 2,000-byte transfer arrived byte-identically for seeds 246 and 999; the channel sent 323 and 299 data packets respectively, showing the cost of losses and retransmissions.

**Task 2:** TODO — run `task2_measure.py` on two labelled networks (five runs each), save your own Wireshark handshake as `out/tcp.pcapng`, and replace this paragraph with the measured medians/spreads, SYN/SYN-ACK/ACK packet numbers, initial sequence numbers, and scaled receive window. No personal measurements or packet capture have been fabricated in this draft.

**Task 3:** The congestion controller uses additive growth and multiplicative backoff. In the local simulation it reached 954.5 goodput/1,000 slots (about 97% of baseline), with 0.1% loss and average queue 4.8; the baseline's higher goodput comes at 37.4% loss and a persistently fuller queue, harming other flows.
