#!/usr/bin/env python3
"""Week 3 - Task 2: DNS chains and resolver steering.

--collect writes raw observations to out/chains.json.
--report reads that file and writes out/report.md.
"""
import argparse
import json
import os
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SITES = [
    "www.microsoft.com", "www.netflix.com", "www.adobe.com",
    "www.cnn.com", "www.apple.com", "www.korea.ac.kr",
    "www.stanford.edu", "www.bbc.co.uk", "www.spotify.com",
    "www.github.com", "www.wikipedia.org", "www.nytimes.com",
]

RESOLVERS = {
    "system": None,
    "google": "8.8.8.8",
    "quad9": "9.9.9.9",
}


def _system_resolver():
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as f:
            for line in f:
                p = line.split()
                if len(p) >= 2 and p[0] == "nameserver":
                    return p[1]
    except OSError:
        pass
    return None


def _q(name, qtype, server, recursive=True):
    # Reuse the packet parser/transport from Task 1.
    sys.path.insert(0, HERE)
    from task1_resolve import _query_packet
    # Task 1's transport is iterative (RD=0); for resolver measurements,
    # a small local copy with RD=1 is used below.
    import random, struct
    ident = random.randrange(1, 65536)
    flags = 0x0100 if recursive else 0
    packet = struct.pack("!HHHHHH", ident, flags, 1, 0, 0, 0)
    from task1_resolve import _encode_name, _parse_message, QTYPE, CLASS_IN
    packet += _encode_name(name) + struct.pack("!HH", QTYPE[qtype], CLASS_IN)
    last = None
    for _ in range(1):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.5)
        try:
            s.sendto(packet, (server, 53))
            while True:
                data, _ = s.recvfrom(8192)
                if len(data) < 12:
                    continue
                rid = struct.unpack("!H", data[:2])[0]
                if rid == ident:
                    flags = struct.unpack("!H", data[2:4])[0]
                    rcode = flags & 0xF
                    return rcode, _parse_message(
                        data, *struct.unpack("!HHHH", data[4:12])
                    )
        except OSError as e:
            last = repr(e)
        finally:
            s.close()
    raise TimeoutError(f"resolver {server} did not answer: {last}")


def _cname_chain(name, server):
    chain = []
    current = name.rstrip(".").lower()
    seen = set()
    for _ in range(12):
        if current in seen:
            break
        seen.add(current)
        rcode, records = _q(current, "A", server, True)
        if rcode:
            break
        cnames = [r["value"].rstrip(".").lower() for r in records
                  if r["section"] == "answer" and r["type"] == 5 and r["value"]]
        chain.append(current)
        if not cnames:
            return chain, current
        current = cnames[0]
    return chain, current


def dig(name, rtype="A", server=None):
    args = ["dig", "+short", name, rtype]
    if server:
        args.insert(1, f"@{server}")
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]


def _answers(name, server):
    try:
        rcode, records = _q(name, "A", server, True)
        if rcode:
            return [], f"rcode={rcode}"
        vals = [r["value"] for r in records
                if r["section"] == "answer" and r["type"] == 1 and r["value"]]
        # Include A answers only; sets are compared irrespective of order.
        return sorted(set(vals)), None
    except Exception as e:
        return [], repr(e)


def collect():
    os.makedirs(OUT, exist_ok=True)
    system = _system_resolver()
    resolved = {k: (system if v is None else v) for k, v in RESOLVERS.items()}
    data = {}
    collection_errors = []

    # Probe each resolver once. A blocked UDP/53 environment should not make
    # the 12-site collection take minutes.
    usable = {}
    for label, server in resolved.items():
        if not server:
            usable[label] = False
            continue
        try:
            _q("dns.google", "A", server, True)
            usable[label] = True
        except Exception as e:
            usable[label] = False
            collection_errors.append(f"{label} ({server}) unavailable: {e!r}")

    chain_template = None
    if system and usable.get("system"):
        try:
            chain_template = _cname_chain("dns.google", system)
        except Exception as e:
            collection_errors.append(f"system chain unavailable: {e!r}")

    for site in SITES:
        item = {"chain": [], "final": None, "answers": {}, "errors": {}}
        if system and usable.get("system"):
            try:
                item["chain"], item["final"] = _cname_chain(site, system)
            except Exception as e:
                item["errors"]["chain"] = repr(e)
        else:
            item["errors"]["chain"] = "system resolver unavailable in this environment"

        for label, server in resolved.items():
            if not server or not usable.get(label):
                item["answers"][label] = []
                item["errors"][label] = "resolver unavailable"
                continue
            vals, err = _answers(site, server)
            item["answers"][label] = vals
            if err:
                item["errors"][label] = err
        item["resolver_servers"] = resolved
        item["collection_errors"] = collection_errors
        data[site] = item

    path = os.path.join(OUT, "chains.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    print(f"wrote {path}")
    if collection_errors:
        print("collection warnings:")
        for e in collection_errors:
            print(" -", e)


# This intentionally simple rule is the one we evaluate.  It is not claimed
# to identify CDN ownership perfectly; the report discusses its false positive.
MULTI_LABEL_PUBLIC_SUFFIXES = {"co.uk", "ac.uk", "org.uk", "com.au", "co.jp", "co.kr"}


def registrable(name):
    labels = name.rstrip(".").lower().split(".")
    if len(labels) < 2:
        return name.lower()
    suffix2 = ".".join(labels[-2:])
    if suffix2 in MULTI_LABEL_PUBLIC_SUFFIXES and len(labels) >= 3:
        return ".".join(labels[-3:])
    return suffix2


def final_zone(name):
    labels = name.rstrip(".").lower().split(".")
    if len(labels) < 2:
        return name.lower()
    suffix2 = ".".join(labels[-2:])
    if suffix2 in MULTI_LABEL_PUBLIC_SUFFIXES and len(labels) >= 3:
        return suffix2
    return suffix2


def report():
    path = os.path.join(OUT, "chains.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    cdn_sites = []
    for site, item in data.items():
        final = item.get("final") or site
        zone = final_zone(final)
        third = registrable(final) != registrable(site)
        # "rule verdict" deliberately uses final-zone ownership heuristic.
        verdict = "third-party" if third else "first-party"
        # For the steering denominator we use the lab's site set: Korea
        # University is the explicit non-CDN control; the other large sites
        # are treated as CDN/distributed-delivery candidates. This avoids
        # equating "has a CNAME" with "is a CDN".
        if site != "www.korea.ac.kr":
            cdn_sites.append(site)
        rows.append((site, len(item.get("chain", [])), zone, third, verdict,
                     item.get("chain", [])))

    steering = 0
    steering_details = []
    for site in cdn_sites:
        answers = data[site].get("answers", {})
        usable = [set(v) for v in answers.values() if v]
        different = len(set(map(tuple, usable))) > 1 if usable else False
        if different:
            steering += 1
        steering_details.append((site, different, answers))

    n = len(cdn_sites)
    measured = sum(
        1 for site in cdn_sites
        if sum(1 for vals in data[site].get("answers", {}).values() if vals) >= 2
    )
    lines = [
        "# Task 2 observation report",
        "",
        "## Classification rule",
        "",
        "I call a site third-party when the final CNAME target has a different "
        "registrable domain from the original site. This is a deliberately "
        "simple ownership heuristic, not proof of CDN ownership.",
        "",
        "| site | chain length | final zone | third party? | rule verdict |",
        "|---|---:|---|---|---|",
    ]
    for site, length, zone, third, verdict, _ in rows:
        lines.append(f"| `{site}` | {length} | `{zone}` | "
                     f"{'yes' if third else 'no'} | {verdict} |")

    lines += [
        "",
        "## Steering",
        "",
        (f"**{steering} of {measured} measured CDN-hosted sites answered differently "
         "to a different resolver.**" if measured else
         "**Steering number: not measurable in this environment because all configured "
         "UDP/53 resolvers timed out. Run `python3 task2_steering.py --collect` on "
         "your network before submission.**"),
        "",
        "A different answer set is evidence that the resolver/CDN path is "
        "steering, but it does not by itself prove geographic nearness: the "
        "three resolvers can be in different networks and anycast can also "
        "affect the observed address.",
        "",
        "## A rule that was wrong",
        "",
        "The heuristic misclassifies `www.wikipedia.org`: its CNAME can end "
        "at `dyna.wikimedia.org`, so a different-registrable-domain test says "
        "third-party even though Wikimedia operates the service itself. "
        "Netflix is the opposite lesson: its own CDN can stay inside "
        "`netflix.com`. Likewise, "
        "a CDN can exist without a visible CNAME (for example, via anycast), "
        "so CNAME presence is not proof of CDN use.",
        "",
        "## Raw resolver answers",
        "",
    ]
    for site, different, answers in steering_details:
        lines.append(f"### `{site}` — {'different' if different else 'same/insufficient'}")
        for label, vals in answers.items():
            lines.append(f"- {label}: {', '.join(vals) if vals else 'no answer'}")
        lines.append("")

    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote out/report.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect()
    elif a.report:
        report()
    else:
        p.print_help()
