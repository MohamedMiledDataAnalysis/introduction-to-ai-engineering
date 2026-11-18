"""Daily monitoring metrics from the request log, and alert rules."""
import json

import pandas as pd

PRICE_PER_M_TOKENS = 3.00     # illustrative blended price, USD per million tokens, for a paid model

THRESHOLDS = {"error_rate": 0.02, "review_rate": 0.10, "p95_seconds": 12.0}


def load_log(path):
    df = pd.DataFrame([json.loads(l) for l in open(path, encoding="utf-8")])
    df["ts"] = pd.to_datetime(df["ts"])
    df["day"] = df["ts"].dt.date
    return df


def daily_metrics(df):
    ok = df[df.status != "error"]
    g = df.groupby(["day", "domain"])
    m = pd.DataFrame({
        "requests": g.size(),
        "error_rate": g.apply(lambda x: (x.status == "error").mean(), include_groups=False),
        "review_rate": ok.groupby(["day", "domain"]).apply(lambda x: (x.status != "verified").mean(), include_groups=False),
        "p50_seconds": ok.groupby(["day", "domain"]).seconds.median(),
        "p95_seconds": ok.groupby(["day", "domain"]).seconds.quantile(0.95),
        "avg_tokens": ok.groupby(["day", "domain"]).tokens.mean(),
        "cost_usd": g.tokens.sum() / 1e6 * PRICE_PER_M_TOKENS,
    }).fillna(0).round(4)
    return m.reset_index()


def alerts(metrics):
    out = []
    for r in metrics.itertuples():
        for metric, limit in THRESHOLDS.items():
            if getattr(r, metric) > limit:
                out.append({"day": r.day, "domain": r.domain, "metric": metric, "value": getattr(r, metric),
                            "limit": limit})
    return pd.DataFrame(out)
