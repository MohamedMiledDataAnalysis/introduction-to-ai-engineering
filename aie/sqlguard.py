"""Run model-written SQL safely: one read-only SELECT on allowed tables, with a row limit."""
import re
import sqlite3

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum|reindex)\b", re.I)


def check_sql(sql, allowed_tables):
    problems = []
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        problems.append("more than one statement")
    if not re.match(r"(?is)^\s*(select|with)\b", s):
        problems.append("not a SELECT query")
    if FORBIDDEN.search(s):
        problems.append(f"forbidden keyword: {FORBIDDEN.search(s).group(0)}")
    for t in re.findall(r"(?i)\b(?:from|join)\s+([a-z_][a-z0-9_]*)", s):
        if t.lower() not in allowed_tables:
            problems.append(f"table not allowed: {t}")
    return problems, s


def run_sql(sql, db="data/am/harbourline.sqlite", allowed_tables=None, max_rows=200):
    allowed = allowed_tables or {"funds", "securities", "holdings", "nav", "benchmark_returns",
                                 "issuer_esg", "transactions"}
    problems, s = check_sql(sql, allowed)
    if problems:
        return {"error": "; ".join(problems)}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)          # the database cannot be changed
    try:
        cur = con.execute(f"SELECT * FROM ({s}) LIMIT {max_rows + 1}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    except sqlite3.Error as err:
        return {"error": f"SQL error: {err}"}
    finally:
        con.close()
    return {"columns": cols, "rows": rows[:max_rows], "truncated": len(rows) > max_rows}


def same_result(a, b, ordered=False, digits=6):
    """Compare two query results by their rows (column names ignored), rounding numbers."""
    if "error" in a or "error" in b:
        return False
    norm = lambda rows: [tuple(round(v, digits) if isinstance(v, float) else v for v in r) for r in rows]
    ra, rb = norm(a["rows"]), norm(b["rows"])
    return ra == rb if ordered else sorted(ra, key=repr) == sorted(rb, key=repr)
