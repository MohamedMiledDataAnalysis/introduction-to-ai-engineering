# Exercise 13.4 - The facts of the HECB commentary
# Run from the root of the repository:  python chapters/ch13/python/solutions/ex13_4_hecb_facts.py

import sys; sys.path.insert(0, ".")

from aie.sqlguard import run_sql
from aie.tools import fund_performance

HECB = "h.fund_code = 'HECB' AND h.month_end = '2026-09-30'"

def one(sql):
    return run_sql(sql)["rows"][0][0]           # the single value of a one-cell result

def hecb_facts_for_prompt():
    p = fund_performance("HECB", 1)
    duration = one(f"""SELECT SUM(h.weight * s.modified_duration) / SUM(h.weight)
                       FROM holdings h JOIN securities s ON h.isin = s.isin
                       WHERE {HECB}""")
    bbb = one(f"""SELECT SUM(h.weight) FROM holdings h JOIN securities s
                  ON h.isin = s.isin WHERE {HECB}
                  AND s.rating IN ('BBB+', 'BBB', 'BBB-')""")
    cash = one(f"SELECT SUM(h.weight) FROM holdings h WHERE {HECB} AND h.isin = 'CASH-EUR'")
    return "\n".join([
        f"- Fund return: {p['fund_return_pct']:.2f}%",
        f"- Benchmark return: {p['benchmark_return_pct']:.2f}%",
        f"- Relative return: {p['relative_return_pct']:+.2f}%",
        f"- Modified duration of the bonds: {duration:.2f} years",
        f"- Share of the bonds rated BBB+ to BBB-: {100 * bbb / (1 - cash):.2f}%",
        f"- Cash: {100 * cash:.2f}%"])

print(hecb_facts_for_prompt())
