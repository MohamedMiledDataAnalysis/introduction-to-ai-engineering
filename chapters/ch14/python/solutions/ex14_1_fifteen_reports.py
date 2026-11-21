# Exercise 14.1 - Fifteen investor reports
# Run from the root of the repository:  python chapters/ch14/python/solutions/ex14_1_fifteen_reports.py

import sys; sys.path.insert(0, ".")

from pathlib import Path
import pandas as pd
from aie.investor_report import (TAPE, month_figures, reconcile,
                                 render_markdown, template_commentary)

dates = sorted(pd.read_csv(TAPE)["RREL6"].unique())[1:]   # no report at closing
Path("reports").mkdir(exist_ok=True)
for d in dates:
    f = month_figures(d)
    ok = all(reconcile(f).values())
    Path(f"reports/larkfield_investor_report_{d[:7].replace('-', '_')}.md") \
        .write_text(render_markdown(f, template_commentary(f)), encoding="utf-8")
    print(d, "PASS" if ok else "FAIL", f"{f['new_defaults']:,.2f}")
