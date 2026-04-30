# readsboparse

*readsb output parser*

A framework for aggregating, filtering, and displaying archived globe_history data produced by [readsb](https://github.com/wiedehopf/readsb).

Requires readsb's globe_history data archival to be enabled. You may need to wait a few hours after enabling it to start aggregating its data. Enable it by adding this argument to `/etc/default/readsb`'s `JSON_OPTIONS` line:
```
--write-globe-history=/var/globe_history
```
Then `sudo systemctl restart readsb`.

Important note: globe_history will get very large over time, as it tracks all aircraft while the option is enabled. Manage your storage accordingly.

This is an independent hobby project. Not affiliated with or endorsed by readsb or its creators.

## Example scripts

* `countries.py`: Aircraft count grouped by country of registration
* `furthest.py`: Furthest captured aircraft
* `military.py`: Captured military aircraft
* `regulars.py`: Aircraft seen on the highest number of distinct days
* `fastest.py`: The fastest captured aircraft
* `furthest_norm.py`: Furthest aircraft normalized by geometric horizon at the aircraft's position. Only really useful as a diagnostic.
* `messages.py`: Highest number of messages received from unique aircraft

## Writing your own scripts

Filters compose. See module docstring for full filter contract.

```python
import readsboparse as rp

# all helicopters under 2000 ft over central NJ
filters = [
    rp.aircraft_type("R44", "B06", "B407"),
    rp.in_bbox(40.0, 41.0, -75.0, -74.0),
    rp.alt_between(0, 2000),
]
for hex_id, meta, pt in rp.scan(filters):
    print(hex_id, pt["lat"], pt["lon"], pt["baro_alt"])
```

## Don't have a feeder?

If you don't have a feeder to provide you with globe_history data, [adsb.lol](https://www.adsb.lol/docs/open-data/historical/) publishes daily community-collected archives. Download a .tar of a day's feed, extract, point TRACE_ROOT at it, and you can sift through a lot of data.
