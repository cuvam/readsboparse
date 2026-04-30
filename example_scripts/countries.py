import json, glob, os, gzip, re, bisect
from collections import Counter
import sys

PRINT_MAX = None # Will print all country counts by default

if len(sys.argv) > 1:
    PRINT_MAX = int(sys.argv[1])

GLOBE_HISTORY = '/var/globe_history'
FLAGS_JS = '/usr/local/share/tar1090/html/flags_93f40979ff2fc40a098d7983c0101a66.js'  # adjust if your tar1090 flags.json lives elsewhere
                                                                                      # (the filename often has a hash interjected in it, like flags_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.json)

# Parse tar1090's ICAO range → country table once.
def load_icao_ranges():
    with open(FLAGS_JS) as f:
        text = f.read()
    # Matches entries like: {start: 0x008000, end: 0x00FFFF, country: "South Africa", ...}
    pattern = re.compile(
        r'start:\s*0x([0-9A-Fa-f]+)\s*,\s*end:\s*0x([0-9A-Fa-f]+)\s*,\s*country:\s*"([^"]+)"'
    )
    ranges = [(int(s, 16), int(e, 16), c) for s, e, c in pattern.findall(text)]
    ranges.sort()
    starts = [r[0] for r in ranges]
    return ranges, starts

ranges, starts = load_icao_ranges()

def icao_country(hex_id):
    n = int(hex_id, 16)
    i = bisect.bisect_right(starts, n) - 1
    while i >= 0 and ranges[i][0] <= n:
        if n <= ranges[i][1]:
            return ranges[i][2]
        i -= 1
    return None

# Collect unique ICAOs
icaos = set()
for path in glob.glob(os.path.join(GLOBE_HISTORY, '*/*/*/traces/*/trace_full_*.json')):
    base = os.path.basename(path)
    if base.startswith('trace_full_') and base.endswith('.json'):
        icaos.add(base[len('trace_full_'):-len('.json')].upper())

countries = Counter()
unknown = 0
for icao in icaos:
    try:
        country = icao_country(icao)
    except ValueError:
        country = None
    if country:
        countries[country] += 1
    else:
        unknown += 1

print(f"Unique aircraft: {len(icaos)}")
print(f"Unique countries: {len(countries)}")
print(f'Unknowns: {unknown}')
synthetic = sum(1 for icao in icaos if icao.startswith('~'))
real_unknown = unknown - synthetic
print(f" - Synthetic (TIS-B/ADS-R): {synthetic}")
print(f" - Genuine unknowns: {real_unknown}")
print(f"\nCountries by aircraft count:" if not PRINT_MAX else f"Top {PRINT_MAX} countries by aircraft count:")
for country, count in countries.most_common()[:PRINT_MAX]:
    print(f"  {count:>5}  {country}")