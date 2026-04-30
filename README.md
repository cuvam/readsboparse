# readsboparse

*readsb output parser*

A framework for aggregating, filtering and displaying archived globe_history data produced by [readsb](https://github.com/wiedehopf/readsb).

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
