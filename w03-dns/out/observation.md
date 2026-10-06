# Week 3 observations

**Task 1:** The root server only knows the delegation to the DNS hierarchy, not the final host address, so the resolver must follow NS referrals until an authoritative A answer is reached. If a referral has no glue A record, I recursively resolve the nameserver's hostname and then continue the original walk; the implementation also retries another server and caps the walk depth.

**Task 2:** I classify a site as third-party when the final CNAME target has a different registrable domain; this deliberately misclassifies `www.wikipedia.org` when it ends at `dyna.wikimedia.org`, because Wikimedia operates the service itself. The steering count must be measured locally with the system, Google, and Quad9 resolvers; UDP/53 is blocked in this execution environment, so I did not invent the number.

**Task 3:** The minimum possible upstream count for this fixed workload is **275**: each name needs one fetch initially and another whenever the previous TTL has expired before its next query, and a correct cache cannot reuse an expired record. My cache reaches exactly 275 upstream calls with zero stale answers; the baseline's fixed 60-second lifetime is both inefficient for short TTLs and incorrect, causing 266 stale answers, worst for the 20-second Microsoft record.
