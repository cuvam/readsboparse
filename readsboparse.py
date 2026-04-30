"""
readsb globe-history trace file reader and filter pipeline.

readsb writes per-aircraft trace files to a globe_history directory tree:
    <root>/YYYY/MM/DD/traces/<last2hex>/trace_full_<hexid>.json

Files may be plain JSON or gzip-compressed (some installs gzip them but
keep the .json extension); load_trace handles both transparently via a
magic-byte sniff.

If the trace files were written without --db-file (so r/t/desc/ownOp are
None), this module can fall back to the wiedehopf tar1090-db CSV at
DB_PATH. The fallback is transparent in `scan()` (controlled by use_db)
and also exposed as `lookup(hex_id)`.

Trace point row layout (indices into each entry of trace['trace']):
    0  t_offset    seconds since trace['timestamp']
    1  lat         degrees, may be None
    2  lon         degrees, may be None
    3  baro_alt    feet, int, or "ground", or None
    4  gs          ground speed, knots, may be None
    5  track       degrees, may be None
    6  flags       bitfield (see readsb docs)
    7  vrate       barometric vertical rate, ft/min, may be None
    8  details     dict of extra fields (callsign, squawk, ...), may be None
    9  src         source string ("adsb_icao", "mlat", ...), may be None
   10  geom_alt    geometric (GPS) altitude, ft, may be None
   11  geom_rate   geometric vertical rate, ft/min, may be None
   12  ias         indicated airspeed, knots, may be None
   13  roll        roll angle, degrees, may be None

Filter contract:
    Every filter is a callable (hex_id, meta, pt) -> bool. `meta` carries
    aircraft-level fields (r, t, desc, ownOp); `pt` carries point-level
    fields (see iter_points). Filters can use any combination. Compose
    with all_of / any_of, or pass any iterable to scan().

Typical usage:

    import readsboparse as rp
    from datetime import date

    filters = [
        rp.aircraft_type("B06", "B407", "B412"),     # helicopters
        rp.in_bbox(40.0, 41.0, -75.0, -74.0),
        rp.alt_between(0, 2000),
    ]
    for hex_id, meta, pt in rp.scan(filters, date=date(2025, 4, 26)):
        ...
"""

import csv
import gzip
import json
from pathlib import Path

TRACE_ROOT = Path("/var/globe_history")
"""Default root of the readsb globe-history tree. Override per-call if needed."""

DB_PATH = Path("/usr/local/share/tar1090/aircraft.csv.gz")
"""Default path to the wiedehopf tar1090-db aircraft.csv.gz database.
Override by reassigning the module attribute or passing path= to lookup()."""

_db_cache = None

def _load_db(path=None):
    """Load and cache the aircraft DB CSV (semicolon-delimited, gzipped).

    Returns a dict mapping lowercase hex id -> row list. Returns an empty
    dict if the file is missing or unreadable. The result is cached for
    the lifetime of the process; the `path` arg only takes effect on the
    very first call.
    """
    global _db_cache
    if _db_cache is not None:
        return _db_cache
    p = Path(path) if path else DB_PATH
    db = {}
    try:
        with gzip.open(p, "rt") as f:
            for row in csv.reader(f, delimiter=";"):
                if row:
                    db[row[0].lower()] = row
    except OSError:
        pass
    _db_cache = db
    return db


def lookup(hex_id, path=None):
    """Look up aircraft metadata by ICAO 24-bit hex id.

    Args:
        hex_id: Hex string, with or without a leading "~" (used for
            non-ICAO/synthetic addresses). Case-insensitive.
        path: Optional override for the DB path on the first call only;
            subsequent calls return cached results.

    Returns:
        Dict with keys 'r', 't', 'desc', 'ownOp'. Values are None when
        the hex is not in the DB or the DB is unavailable.
    """
    db = _load_db(path)
    info = db.get(hex_id.lstrip("~").lower(), [])
    return {
        "r":     info[1] if len(info) > 1 else None,
        "t":     info[2] if len(info) > 2 else None,
        "desc":  info[4] if len(info) > 4 else None,
        "ownOp": info[5] if len(info) > 5 else None,
    }


def iter_trace_files(root=TRACE_ROOT, date=None):
    """Walk the globe-history tree and yield every trace_full file found.

    Args:
        root: Path to the globe_history root directory.
        date: Optional datetime.date. If given, only that day's subtree
            (root/YYYY/MM/DD) is walked. Otherwise the entire tree is walked.

    Yields:
        (path, hex_id) tuples, where `path` is a pathlib.Path to the trace
        file and `hex_id` is the lowercase ICAO 24-bit hex address as a string
        (e.g. "a1b2c3"). Military/non-ICAO addresses may be prefixed with "~".
    """
    base = root if date is None else root / f"{date.year:04d}/{date.month:02d}/{date.day:02d}"
    for p in base.rglob("trace_full_*.json*"):
        hex_id = p.stem.removeprefix("trace_full_").removesuffix(".json")
        yield p, hex_id


def load_trace(path):
    """Load and parse one trace JSON file (gzipped or plain).

    Detects gzip by the 0x1f8b magic bytes, so it works whether the file
    is *.json.gz, plain *.json, or gzip-with-a-.json-extension.

    Args:
        path: Path to a trace_full_* file.

    Returns:
        The parsed JSON document as a dict. Top-level keys typically
        include 'icao', 'r', 't', 'desc', 'ownOp', 'timestamp' (unix
        seconds, the t=0 reference for the trace), and 'trace' (list of
        point rows; see module docstring for layout).

    Raises:
        OSError: if the file cannot be opened or decompressed.
        json.JSONDecodeError: if the contents are not valid JSON.
    """
    with open(path, "rb") as f:
        magic = f.read(2)
    opener = gzip.open if magic == b"\x1f\x8b" else open
    with opener(path, "rt") as f:
        return json.load(f)


def iter_points(trace):
    """Yield each point in a loaded trace as a flat dict.

    All trace row fields are exposed. Short rows (older readsb versions
    or partial records) get None for missing trailing fields.

    Args:
        trace: A dict as returned by `load_trace`.

    Yields:
        Dicts with keys:
            ts         absolute unix timestamp of the sample (float seconds)
            lat        degrees or None
            lon        degrees or None
            baro_alt   feet (int), the string "ground", or None
            gs         ground speed in knots or None
            track      degrees or None
            flags      bitfield int or None
            vrate      barometric vertical rate, ft/min, or None
            details    dict (callsign, squawk, ...) or None
            src        source string ("adsb_icao", "mlat", ...) or None
            geom_alt   geometric altitude, ft, or None
            geom_rate  geometric vertical rate, ft/min, or None
            ias        indicated airspeed, knots, or None
            roll       roll angle, degrees, or None
    """
    t0 = trace["timestamp"]
    for row in trace.get("trace", []):
        n = len(row)
        yield {
            "ts":        t0 + row[0],
            "lat":       row[1],
            "lon":       row[2],
            "baro_alt":  row[3],
            "gs":        row[4],
            "track":     row[5],
            "flags":     row[6],
            "vrate":     row[7],
            "details":   row[8]  if n > 8  else None,
            "src":       row[9]  if n > 9  else None,
            "geom_alt":  row[10] if n > 10 else None,
            "geom_rate": row[11] if n > 11 else None,
            "ias":       row[12] if n > 12 else None,
            "roll":      row[13] if n > 13 else None,
        }


# --- filter constructors -----------------------------------------------------
# Every filter is a callable (hex_id, meta, pt) -> bool. Aircraft-level
# filters look at hex_id/meta and ignore pt; point-level filters do the
# opposite. Compose with all_of / any_of, or pass any iterable to scan().


# Aircraft-level filters

def aircraft_type(*codes):
    """Filter: meta['t'] (ICAO type code, e.g. 'B407', 'GLF6') in `codes`."""
    cs = set(codes)
    return lambda hex_id, meta, pt: meta.get("t") in cs


def aircraft_reg(*regs):
    """Filter: meta['r'] (registration, e.g. 'N406TD') in `regs`."""
    rs = set(regs)
    return lambda hex_id, meta, pt: meta.get("r") in rs


def desc_contains(substring):
    """Filter: case-insensitive substring match against meta['desc']."""
    s = substring.lower()
    return lambda hex_id, meta, pt: s in (meta.get("desc") or "").lower()


# Point-level filters

def in_bbox(lat_min, lat_max, lon_min, lon_max):
    """Filter: point lies within an inclusive lat/lon bounding box.

    Points missing lat or lon are rejected. Does not handle antimeridian
    crossing (lon_min must be <= lon_max numerically).
    """
    def f(hex_id, meta, pt):
        return (pt["lat"] is not None and pt["lon"] is not None
                and lat_min <= pt["lat"] <= lat_max
                and lon_min <= pt["lon"] <= lon_max)
    return f


def alt_between(lo, hi):
    """Filter: barometric altitude in [lo, hi] feet.

    Rejects points with baro_alt of None or "ground".
    """
    def f(hex_id, meta, pt):
        a = pt["baro_alt"]
        if a is None or a == "ground":
            return False
        return lo <= a <= hi
    return f


def time_between(t_lo, t_hi):
    """Filter: sample timestamp in [t_lo, t_hi], both unix seconds."""
    return lambda hex_id, meta, pt: t_lo <= pt["ts"] <= t_hi


# Composition

def all_of(*filters):
    """Combine filters with logical AND. Empty call returns a pass-all filter."""
    return lambda hex_id, meta, pt: all(f(hex_id, meta, pt) for f in filters)


def any_of(*filters):
    """Combine filters with logical OR. Empty call returns a reject-all filter."""
    return lambda hex_id, meta, pt: any(f(hex_id, meta, pt) for f in filters)


# --- main pipeline -----------------------------------------------------------


def scan(filters, root=TRACE_ROOT, date=None, use_db=True):
    """Stream every matching point across all trace files under `root`.

    Args:
        filters: Iterable of (hex_id, meta, pt) -> bool callables. A point
            is emitted only if all of them return True. Pass an empty
            list / None for no filtering.
        root: Globe-history root directory.
        date: Optional datetime.date to restrict the walk to one day.
        use_db: If True (default) and the trace's own metadata has no
            registration, fall back to looking up the hex in DB_PATH.
            Set False to skip the DB entirely.

    Yields:
        (hex_id, meta, pt) tuples where:
            hex_id  ICAO hex string (from filename)
            meta    dict with keys 'r', 't', 'desc', 'ownOp' (values may
                    be None if neither the trace nor the DB has them)
            pt      point dict as produced by iter_points

    Files that fail to open or parse are silently skipped.
    """
    keep = all_of(*filters) if filters else lambda h, m, p: True
    for path, hex_id in iter_trace_files(root, date):
        try:
            tr = load_trace(path)
        except (OSError, json.JSONDecodeError):
            continue
        meta = {k: tr.get(k) for k in ("r", "t", "desc", "ownOp")}
        if use_db and not meta.get("r"):
            meta = lookup(hex_id)
        for pt in iter_points(tr):
            if keep(hex_id, meta, pt):
                yield hex_id, meta, pt