"""Load the Harbourline CSV files into a SQLite database: data/am/harbourline.sqlite."""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
db = ROOT / "data/am/harbourline.sqlite"
db.unlink(missing_ok=True)
con = sqlite3.connect(db)
pd.read_csv(ROOT / "data/am/funds.csv").to_sql("funds", con, index=False)
pd.read_csv(ROOT / "data/am/security_master.csv").to_sql("securities", con, index=False)
h = pd.read_csv(ROOT / "data/am/fund_holdings_monthly.csv")
h.to_sql("holdings", con, index=False)
pd.read_csv(ROOT / "data/am/fund_nav_monthly.csv").to_sql("nav", con, index=False)
bm = pd.read_csv(ROOT / "data/am/benchmark_returns_monthly.csv").melt(id_vars="month_end", var_name="fund_code",
                                                                     value_name="benchmark_return")
bm.to_sql("benchmark_returns", con, index=False)
pd.read_csv(ROOT / "data/am/issuer_esg.csv").to_sql("issuer_esg", con, index=False)
pd.read_csv(ROOT / "data/am/transactions_2026_09.csv").to_sql("transactions", con, index=False)
con.execute("CREATE INDEX ix_hold ON holdings(fund_code, month_end)")
con.commit()
for t in ["funds", "securities", "holdings", "nav", "benchmark_returns", "issuer_esg", "transactions"]:
    print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
con.close()
