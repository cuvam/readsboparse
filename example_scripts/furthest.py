#!/usr/bin/env python3
"""Top 10 furthest decode positions, one per aircraft."""

from math import radians, sin, cos, asin, sqrt
import readsboparse as rp
import sys

PRINT_MAX = 20

if len(sys.argv) > 1:
    PRINT_MAX = int(sys.argv[1])

QTH_LAT = 40.42
QTH_LON = -74.06

def haversine_nmi(lat1, lon1, lat2, lon2):
    R_NMI = 3440.065
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R_NMI * asin(sqrt(a))

def main():
    has_pos = rp.in_bbox(-90, 90, -180, 180)
    best_per_ac = {}  # hex_id -> (distance, meta, pt)

    for hex_id, meta, pt in rp.scan([has_pos]):
        d = haversine_nmi(QTH_LAT, QTH_LON, pt["lat"], pt["lon"])
        cur = best_per_ac.get(hex_id)
        if cur is None or d > cur[0]:
            best_per_ac[hex_id] = (d, meta, pt)

    ranked = sorted(best_per_ac.items(), key=lambda kv: kv[1][0], reverse=True)

    print(f"{'#':>2}  {'dist_nmi':>9}  {'hex':>7}  {'reg':>10}  {'type':>6}  {'alt':>6}  desc")
    for i, (hex_id, (d, meta, pt)) in enumerate(ranked[:PRINT_MAX], 1):
        alt = pt["baro_alt"]
        alt_s = f"{alt}" if isinstance(alt, int) else str(alt or '')
        print(f"{i:>2}  {d:>9.1f}  {hex_id:>7}  {str(meta.get('r') or ''):>10}  "
              f"{str(meta.get('t') or ''):>6}  {alt_s:>6}  {meta.get('desc') or ''}")

if __name__ == '__main__':
    main()