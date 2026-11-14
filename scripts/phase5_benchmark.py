"""Small, reproducible HTTP latency probe; no training, trading or synthetic success data."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import statistics
from time import perf_counter

import httpx


def summarize(rows):
    times = sorted(row["milliseconds"] for row in rows if row["status"] == 200)
    return {"requests": len(rows), "successes": len(times), "failures": len(rows) - len(times),
            "median_ms": statistics.median(times) if times else None,
            "p95_nearest_rank_ms": times[math.ceil(.95 * len(times)) - 1] if times else None,
            "max_ms": max(times) if times else None, "observations": rows}


async def benchmark(base_url, output):
    async with httpx.AsyncClient(base_url=base_url, timeout=60, trust_env=False) as client:
        health = await client.get("/health")
        health.raise_for_status()
        if health.json().get("environment") != "acceptance":
            raise RuntimeError("Refusing to benchmark outside the isolated acceptance environment.")

        async def probe(path):
            started = perf_counter()
            try:
                response = await client.get(path)
                return {"milliseconds": (perf_counter() - started) * 1000,
                        "status": response.status_code, "response_bytes": len(response.content)}
            except httpx.HTTPError as exc:
                return {"milliseconds": (perf_counter() - started) * 1000,
                        "status": 0, "error_type": type(exc).__name__}

        groups = {}
        for name, path, count in (
            ("health_serial", "/health", 30), ("readiness_serial", "/ready", 30),
            ("history_250_bars", "/api/stocks/history?symbol=HPG&limit=250", 10),
            ("prediction_serial", "/api/predict/signal?symbol=HPG&model_type=lightgbm", 5),
        ):
            await probe(path)  # Explicit warm-up, excluded from reported timings.
            groups[name] = summarize([await probe(path) for _ in range(count)])

        semaphore = asyncio.Semaphore(5)
        async def limited_health():
            async with semaphore:
                return await probe("/health")

        results = await asyncio.gather(*[limited_health() for _ in range(30)],
            probe("/api/predict/signal?symbol=HPG&model_type=lightgbm"))
        groups["health_concurrent_with_prediction"] = summarize(results[:-1])
        groups["prediction_during_health_burst"] = summarize(results[-1:])
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "base_url": base_url,
              "transport": "real HTTP to isolated Docker API", "client_platform": platform.platform(),
              "health_concurrency_limit": 5, "warm_up_excluded": True, "results": groups,
              "limitations": ["Local machine, not a production capacity test.",
                  "Small samples; p95 is nearest-rank and not a confidence bound.",
                  "No browser FPS, network WAN or distributed load was measured."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({name: {k: v for k, v in values.items() if k != "observations"}
                      for name, values in groups.items()}, indent=2))
    if any(group["failures"] for group in groups.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(benchmark(args.base_url, args.output))
