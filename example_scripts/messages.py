#!/usr/bin/env python3
"""Top N aircraft by total message count in archive."""
import sys
import readsboparse as rp


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    counts = {}  # hex_id -> (count, meta)
    for hex_id, meta, pt in rp.scan([]):
        if hex_id in counts:
            counts[hex_id] = (counts[hex_id][0] + 1, meta)
        else:
            counts[hex_id] = (1, meta)

    ranked = sorted(counts.items(), key=lambda kv: kv[1][0], reverse=True)
    print(f"{'#':>2}  {'msgs':>7}  {'hex':>7}  {'reg':>10}  {'type':>6}  desc")
    for i, (hex_id, (count, meta)) in enumerate(ranked[:n], 1):
        print(f"{i:>2}  {count:>7}  {hex_id:>7}  {str(meta.get('r') or ''):>10}  "
              f"{str(meta.get('t') or ''):>6}  {meta.get('desc') or ''}")


if __name__ == '__main__':
    main()