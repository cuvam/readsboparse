#!/usr/bin/env python3
"""Top N furthest decode positions normalized by geometric horizon at altitude."""
from math import radians, sin, cos, asin, sqrt
import readsboparse as rp

QTH_LAT = 40.42
QTH_LON = -74.06
MIN_ALT_FT = 1000


def haversine_nmi(lat1, lon1, lat2, lon2):
    R_NMI = 3440.065
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R_NMI * asin(sqrt(a))


def horizon_nmi(alt_ft):
    R_NMI = 3440.065
    alt_nmi = alt_ft / 6076.12
    return sqrt(2 * R_NMI * alt_nmi + alt_nmi ** 2)


def main():
    has_pos = rp.in_bbox(-90, 90, -180, 180)
    best_per_ac = {}
    for hex_id, meta, pt in rp.scan([has_pos]):
        src = pt.get("src")
        if src != "adsb_icao":
            continue
        alt = pt["baro_alt"]
        if not isinstance(alt, int) or alt < MIN_ALT_FT:
            continue
        d = haversine_nmi(QTH_LAT, QTH_LON, pt["lat"], pt["lon"])
        h = horizon_nmi(alt)
        if d > h * 1.05:  # reject geometrically impossible points (5% margin for ducting)
            continue
        frac = d / h
        alt = pt["baro_alt"]
        if not isinstance(alt, int) or alt < MIN_ALT_FT:
            continue
        d = haversine_nmi(QTH_LAT, QTH_LON, pt["lat"], pt["lon"])
        frac = d / horizon_nmi(alt)
        cur = best_per_ac.get(hex_id)
        if cur is None or frac > cur[0]:
            best_per_ac[hex_id] = (frac, d, alt, meta, pt)

    ranked = sorted(best_per_ac.items(), key=lambda kv: kv[1][0], reverse=True)
    print(f"{'#':>2}  {'frac':>5}  {'dist':>6}  {'horizon':>7}  {'hex':>7}  {'reg':>10}  {'type':>6}  {'alt':>6}  desc")
    for i, (hex_id, (frac, d, alt, meta, pt)) in enumerate(ranked[:30], 1):
        h = horizon_nmi(alt)
        print(f"{i:>2}  {frac:>5.2f}  {d:>6.1f}  {h:>7.1f}  {hex_id:>7}  "
              f"{str(meta.get('r') or ''):>10}  {str(meta.get('t') or ''):>6}  "
              f"{alt:>6}  {meta.get('desc') or ''}")


if __name__ == '__main__':
    main()