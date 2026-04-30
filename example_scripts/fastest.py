#!/usr/bin/env python3
"""Top N fastest decode positions, one per aircraft."""
from math import radians, sin, cos, asin, sqrt
import readsboparse as rp
import sys

PRINT_MAX = 20

if len(sys.argv) > 1:
    PRINT_MAX = int(sys.argv[1])

def main():
    has_pos = rp.in_bbox(-90, 90, -180, 180)
    best_per_ac = {}  # hex_id -> (gs, alt, meta, pt)
    for hex_id, meta, pt in rp.scan([has_pos]):
        gs = pt["gs"]
        if not isinstance(gs, (int, float)):
            continue
        cur = best_per_ac.get(hex_id)
        if cur is None or gs > cur[0]:
            best_per_ac[hex_id] = (gs, pt["baro_alt"], meta, pt)

    ranked = sorted(best_per_ac.items(), key=lambda kv: kv[1][0], reverse=True)
    print(f"{'#':>2}  {'gs_kt':>6}  {'hex':>7}  {'reg':>10}  {'type':>6}  {'alt':>6}  desc")
    for i, (hex_id, (gs, alt, meta, pt)) in enumerate(ranked[:PRINT_MAX], 1):
        alt_s = f"{alt}" if isinstance(alt, int) else str(alt or '')
        print(f"{i:>2}  {gs:>6.1f}  {hex_id:>7}  {str(meta.get('r') or ''):>10}  "
              f"{str(meta.get('t') or ''):>6}  {alt_s:>6}  {meta.get('desc') or ''}")


if __name__ == '__main__':
    main()