#!/usr/bin/env python3
"""Top N aircraft by number of distinct days seen in archive. Will require a lot more data to not cluster."""
import sys
from datetime import datetime, timezone
import readsboparse as rp


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    days_per_ac = {}  # hex_id -> (set of dates, meta)
    for hex_id, meta, pt in rp.scan([]):
        d = datetime.fromtimestamp(pt["ts"], tz=timezone.utc).date()
        if hex_id in days_per_ac:
            days_per_ac[hex_id][0].add(d)
        else:
            days_per_ac[hex_id] = ({d}, meta)

    ranked = sorted(days_per_ac.items(), key=lambda kv: len(kv[1][0]), reverse=True)
    print(f"{'#':>2}  {'days':>4}  {'hex':>7}  {'reg':>10}  {'type':>6}  desc")
    for i, (hex_id, (dates, meta)) in enumerate(ranked[:n], 1):
        print(f"{i:>2}  {len(dates):>4}  {hex_id:>7}  {str(meta.get('r') or ''):>10}  "
              f"{str(meta.get('t') or ''):>6}  {meta.get('desc') or ''}")


if __name__ == '__main__':
    main()