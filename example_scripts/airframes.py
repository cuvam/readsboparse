"""
Counts most commonly captured airframes by ICAO type code.

Aircraft without type data (in trace metadata or DB fallback) are excluded.
"""

import json
import sys
from collections import Counter

import readsboparse as rp

PRINT_MAX = None

if len(sys.argv) > 1:
    PRINT_MAX = int(sys.argv[1])

seen = {}
descs = {}

for path, hex_id in rp.iter_trace_files():
    if hex_id in seen:
        continue
    try:
        tr = rp.load_trace(path)
    except (OSError, json.JSONDecodeError):
        continue
    meta = {k: tr.get(k) for k in ("r", "t", "desc", "ownOp")}
    if not meta.get("r"):
        meta = rp.lookup(hex_id)
    t = meta.get("t")
    seen[hex_id] = t
    if t and t not in descs and meta.get("desc"):
        descs[t] = meta["desc"]

types = Counter(t for t in seen.values() if t)
excluded = sum(1 for t in seen.values() if not t)

print(f"Unique aircraft with type data: {sum(types.values())}")
print(f"Unique airframe types: {len(types)}")
print(f"Excluded (no type data): {excluded}")
print(f"\nAirframes by aircraft count:" if not PRINT_MAX else f"Top {PRINT_MAX} airframes by aircraft count:")
for t, count in types.most_common()[:PRINT_MAX]:
    print(f"  {count:>5}  {t:<6}  {descs.get(t, '')}")