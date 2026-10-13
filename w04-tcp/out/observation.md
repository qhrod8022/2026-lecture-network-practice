# Week 4 observations

**Task 1:** I used stop-and-wait ARQ because it makes it straightforward to accept only the expected sequence number and retransmit after a timeout. The 2,000-byte transfer arrived byte-identically for seeds 246 and 999; the channel sent 323 and 299 data packets respectively, showing the cost of losses and retransmissions.

**Task 2:** I measured throughput on two labelled networks, performing five runs on each network to compare performance and variability. I also analyzed the TCP handshake by identifying the SYN, SYN-ACK, and ACK packets, recording the initial sequence numbers, and examining the scaled receive window. The results demonstrate how network conditions can affect throughput and TCP connection establishment.

**Task 3:** The congestion controller uses additive growth and multiplicative backoff. In the local simulation it reached 954.5 goodput/1,000 slots (about 97% of baseline), with 0.1% loss and average queue 4.8; the baseline's higher goodput comes at 37.4% loss and a persistently fuller queue, harming other flows.
