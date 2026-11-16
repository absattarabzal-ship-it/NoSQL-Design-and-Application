# benchmark.py
import csv, math, statistics
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
coll = client.nosql_lab12.orders

QUERY = {"customerId": 10, "status": "DELIVERING"}  # AP-01

def one():
    start = perf_counter()
    try:
        list(coll.find(QUERY).limit(100))
        return ((perf_counter() - start) * 1000, True)
    except Exception:
        return ((perf_counter() - start) * 1000, False)

def percentile(v, p):
    v = sorted(v)
    if not v:
        return float("nan")
    idx = (len(v) - 1) * p / 100
    lo, hi = math.floor(idx), math.ceil(idx)
    return v[lo] + (v[hi] - v[lo]) * (idx - lo)

def run(mode, workers=4, n=400):
    for _ in range(40):      # warm-up отдельно
        one()
    t0 = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: one(), range(n)))
    seconds = perf_counter() - t0
    lat = [ms for ms, ok in results if ok]
    success = len(lat)
    return {
        "mode": mode, "workers": workers, "repeat": None,
        "rps": round(success / seconds, 2),
        "p50": round(percentile(lat, 50), 2),
        "p95": round(percentile(lat, 95), 2),
        "p99": round(percentile(lat, 99), 2),
        "errors": n - success,
        "duration_s": round(seconds, 2),
    }

if __name__ == "__main__":
    rows = []
    for mode in ["no_index", "with_index"]:
        for workers in [1, 4, 8]:
            for repeat in range(1, 4):
                r = run(mode, workers=workers, n=400)
                r["repeat"] = repeat
                rows.append(r)
                print(r)
    with open("results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)