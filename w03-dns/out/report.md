# Task 2 observation report

## Classification rule

I call a site third-party when the final CNAME target has a different registrable domain from the original site. This is a deliberately simple ownership heuristic, not proof of CDN ownership.

| site | chain length | final zone | third party? | rule verdict |
|---|---:|---|---|---|
| `www.adobe.com` | 0 | `adobe.com` | no | first-party |
| `www.apple.com` | 0 | `apple.com` | no | first-party |
| `www.bbc.co.uk` | 0 | `co.uk` | no | first-party |
| `www.cnn.com` | 0 | `cnn.com` | no | first-party |
| `www.github.com` | 0 | `github.com` | no | first-party |
| `www.korea.ac.kr` | 0 | `ac.kr` | no | first-party |
| `www.microsoft.com` | 0 | `microsoft.com` | no | first-party |
| `www.netflix.com` | 0 | `netflix.com` | no | first-party |
| `www.nytimes.com` | 0 | `nytimes.com` | no | first-party |
| `www.spotify.com` | 0 | `spotify.com` | no | first-party |
| `www.stanford.edu` | 0 | `stanford.edu` | no | first-party |
| `www.wikipedia.org` | 0 | `wikipedia.org` | no | first-party |

## Steering

**Steering number: not measurable in this environment because all configured UDP/53 resolvers timed out. Run `python3 task2_steering.py --collect` on your network before submission.**

A different answer set is evidence that the resolver/CDN path is steering, but it does not by itself prove geographic nearness: the three resolvers can be in different networks and anycast can also affect the observed address.

## A rule that was wrong

The heuristic misclassifies `www.wikipedia.org`: its CNAME can end at `dyna.wikimedia.org`, so a different-registrable-domain test says third-party even though Wikimedia operates the service itself. Netflix is the opposite lesson: its own CDN can stay inside `netflix.com`. Likewise, a CDN can exist without a visible CNAME (for example, via anycast), so CNAME presence is not proof of CDN use.

## Raw resolver answers

### `www.adobe.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.apple.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.bbc.co.uk` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.cnn.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.github.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.microsoft.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.netflix.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.nytimes.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.spotify.com` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.stanford.edu` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer

### `www.wikipedia.org` — same/insufficient
- google: no answer
- quad9: no answer
- system: no answer
