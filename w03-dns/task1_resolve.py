#!/usr/bin/env python3
"""Week 3 Task 1 - a small iterative DNS resolver.

The resolver sends DNS queries with RD=0 and follows root -> TLD ->
authoritative delegations itself.  It also handles missing glue by resolving
the nameserver name recursively, retries other nameservers, follows CNAMEs,
and caps recursion depth.
"""
import argparse
import random
import socket
import struct
import subprocess
import sys

ROOT_SERVERS = [
    "198.41.0.4", "199.9.14.201", "192.33.4.12",
]

VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]

QTYPE = {"A": 1, "NS": 2, "CNAME": 5}
CLASS_IN = 1


def _encode_name(name):
    name = name.rstrip(".")
    if not name:
        return b"\0"
    return b"".join(bytes([len(p)]) + p.encode("idna") for p in name.split(".")) + b"\0"


def _decode_name(msg, off):
    labels, jumped, end = [], False, off
    seen = set()
    while True:
        if off >= len(msg):
            raise ValueError("truncated DNS name")
        if off in seen:
            raise ValueError("DNS compression loop")
        seen.add(off)
        n = msg[off]
        if n == 0:
            off += 1
            if not jumped:
                end = off
            return ".".join(labels), end
        if n & 0xC0 == 0xC0:
            if off + 1 >= len(msg):
                raise ValueError("truncated DNS pointer")
            ptr = ((n & 0x3F) << 8) | msg[off + 1]
            if not jumped:
                end = off + 2
            off = ptr
            jumped = True
            continue
        if n & 0xC0:
            raise ValueError("bad label")
        off += 1
        if off + n > len(msg):
            raise ValueError("truncated DNS label")
        labels.append(msg[off:off+n].decode("idna"))
        off += n
        if not jumped:
            end = off


def _query_packet(name, qtype, server, timeout=2.0):
    ident = random.randrange(1, 65536)
    flags = 0  # RD=0: iterative query
    packet = struct.pack("!HHHHHH", ident, flags, 1, 0, 0, 0)
    packet += _encode_name(name) + struct.pack("!HH", QTYPE[qtype], CLASS_IN)

    last = None
    for _ in range(2):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(packet, (server, 53))
            while True:
                data, _ = s.recvfrom(4096)
                if len(data) < 12:
                    continue
                rid, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", data[:12])
                if rid != ident:
                    continue
                return _parse_message(data, qd, an, ns, ar)
        except OSError as e:
            last = e
        finally:
            s.close()
    raise TimeoutError(f"{server} did not answer: {last}")


def _parse_message(msg, qd, an, ns, ar):
    off = 12
    for _ in range(qd):
        _, off = _decode_name(msg, off)
        off += 4

    records = []
    for section, count in (("answer", an), ("authority", ns), ("additional", ar)):
        for _ in range(count):
            name, off = _decode_name(msg, off)
            if off + 10 > len(msg):
                raise ValueError("truncated RR")
            typ, cls, ttl, rdlen = struct.unpack("!HHIH", msg[off:off+10])
            off += 10
            rstart = off
            if off + rdlen > len(msg):
                raise ValueError("truncated RDATA")
            if typ in (QTYPE["NS"], QTYPE["CNAME"]):
                value, _ = _decode_name(msg, off)
            elif typ == QTYPE["A"] and rdlen == 4:
                value = socket.inet_ntoa(msg[off:off+4])
            else:
                value = None
            off = rstart + rdlen
            records.append({"section": section, "name": name.rstrip(".").lower(),
                             "type": typ, "ttl": ttl, "value": value})
    return records


def dig_answer(name):
    """Comparison helper used by the supplied verifier when dig is available."""
    try:
        out = subprocess.run(["dig", "+short", name, "A"],
                             capture_output=True, text=True, timeout=4).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l for l in out.split() if l and l[0].isdigit()]


class Resolver:
    MAX_DEPTH = 12
    QUERY_TIMEOUT = 2.0

    def _resolve_ns_name(self, ns_name, path, depth):
        # A nameserver name without glue needs its own DNS walk.
        addr, _ = self._walk(ns_name, path, depth + 1)
        return addr

    def _walk(self, name, path, depth):
        if depth > self.MAX_DEPTH:
            raise RuntimeError("maximum DNS walk depth exceeded")
        current = name.rstrip(".").lower()
        servers = list(ROOT_SERVERS)

        # Each delegation is followed until an answer is found.
        for _level in range(self.MAX_DEPTH):
            next_servers = []
            last_error = None
            for server in servers:
                path.append(server)
                try:
                    records = _query_packet(current, "A", server, self.QUERY_TIMEOUT)
                except (OSError, TimeoutError, ValueError) as e:
                    last_error = e
                    continue

                # An A answer is authoritative enough for this iterative walk.
                for r in records:
                    if r["section"] == "answer" and r["type"] == QTYPE["A"] and r["value"]:
                        return r["value"], path

                cnames = [r["value"] for r in records
                          if r["section"] == "answer" and r["type"] == QTYPE["CNAME"] and r["value"]]
                if cnames:
                    # Restart at root for the canonical target.
                    return self._walk(cnames[0], path, depth + 1)

                ns_records = [r for r in records
                              if r["section"] == "authority" and r["type"] == QTYPE["NS"] and r["value"]]
                if not ns_records:
                    continue

                glue = {r["name"]: r["value"] for r in records
                        if r["section"] == "additional" and r["type"] == QTYPE["A"] and r["value"]}
                for ns in ns_records:
                    a = glue.get(ns["value"].rstrip(".").lower())
                    if a:
                        next_servers.append(a)
                if not next_servers:
                    # No glue: resolve the NS name itself, extending the path.
                    for ns in ns_records:
                        try:
                            a = self._resolve_ns_name(ns["value"], path, depth + 1)
                            next_servers.append(a)
                        except Exception:
                            continue
                if next_servers:
                    break

            if next_servers:
                # De-duplicate while preserving order.
                seen = set()
                servers = [x for x in next_servers if not (x in seen or seen.add(x))]
                continue
            raise RuntimeError(f"no usable delegation for {current}: {last_error}")
        raise RuntimeError(f"too many delegation levels for {name}")

    def resolve(self, name):
        path = []
        address, _ = self._walk(name, path, 0)
        return address, path


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if expected and addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- CDN answer may differ between queries"
        elif not expected:
            note = "  <- dig unavailable; iterative answer obtained"
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    if a.verify:
        sys.exit(verify())
    addr, path = Resolver().resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")


if __name__ == "__main__":
    main()
