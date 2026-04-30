#!/usr/bin/env python3
"""List unique military aircraft in globe_history, using ranges.json from tar1090. Will not work if tar1090 is not installed."""

import gzip
import json
import glob
import os
import sys

PRINT_MAX = None

if len(sys.argv) > 1:
    PRINT_MAX = int(sys.argv[1])

GLOBE_HISTORY = '/var/globe_history'
DB_DIR = '/usr/local/share/tar1090/git-db/db'
RANGES_FILE = '/usr/local/share/tar1090/git-db/ranges.json'


def load_mil_ranges():
    with open(RANGES_FILE) as f:
        ranges = json.load(f)
    return [(int(s, 16), int(e, 16)) for s, e in ranges['military']]


def is_military(icao_int, ranges):
    for start, end in ranges:
        if start <= icao_int <= end:
            return True
    return False


db_cache = {}
def lookup(icao):
    icao = icao.upper()
    for plen in [3, 2, 1]:
        bkey, dkey = icao[:plen], icao[plen:]
        path = f'{DB_DIR}/{bkey}.js'
        if path not in db_cache:
            try:
                with gzip.open(path, 'rt') as f:
                    db_cache[path] = json.load(f)
            except (FileNotFoundError, OSError):
                db_cache[path] = None
        shard = db_cache[path]
        if shard and dkey in shard:
            entry = shard[dkey]
            return {'reg': entry[0], 'type': entry[1], 'flags': entry[2], 'desc': entry[3]}
    return None


def main():
    ranges = load_mil_ranges()

    icaos = set()
    for path in glob.glob(os.path.join(GLOBE_HISTORY, '*/*/*/traces/*/trace_full_*.json')):
        base = os.path.basename(path)
        if base.startswith('trace_full_') and base.endswith('.json'):
            icaos.add(base[len('trace_full_'):-len('.json')].upper())

    mil = []
    for icao in icaos:
        try:
            h = int(icao, 16)
        except ValueError:
            continue
        if is_military(h, ranges):
            entry = lookup(icao) or {}
            mil.append((icao, entry.get('reg'), entry.get('type'), entry.get('desc')))

    mil.sort()
    print(f"Military aircraft confirmed: {len(mil)}\n")
    print(f"{'icao':>8}  {'reg':>10}  {'type':>6}  desc")
    for icao, reg, typ, desc in mil[:PRINT_MAX]:
        print(f"{icao:>8}  {str(reg or ''):>10}  {str(typ or ''):>6}  {desc or ''}")


if __name__ == '__main__':
    main()
