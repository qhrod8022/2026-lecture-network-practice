#!/usr/bin/env python3
"""Week 4 · Task 3 — congestion control using ACK/loss feedback."""

class FixedWindow:
    """Unadaptive baseline: always send 64 packets in flight."""
    def __init__(self): self.window = 64
    def on_ack(self): pass
    def on_loss(self): pass

class YourControl:
    """AIMD-style control with gentle additive growth and multiplicative backoff."""
    def __init__(self):
        self.window = 10.0
        self._acks = 0
    def on_ack(self):
        self._acks += 1
        # Additive increase: grow slowly so the queue does not stay saturated.
        if self._acks >= max(1, int(self.window)):
            self.window += 0.35
            self._acks = 0
        self.window = min(self.window, 30.0)
    def on_loss(self):
        # Multiplicative decrease after a timeout.
        self.window = max(2.0, self.window * 0.72)
        self._acks = 0
