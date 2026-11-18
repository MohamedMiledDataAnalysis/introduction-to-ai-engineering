"""Run model-written SQL safely: one read-only SELECT on allowed tables, with a row limit."""
import re
import sqlite3
import time

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace\s+into|vacuum|reindex)\b",
                       re.I)
CLAUSE_END = re.compile(r"(?i)\b(where|group|order|having|limit|union|except|intersect|on|using)\b|\)")


def tables_in(sql):
    """Every table named after FROM or JOIN, including comma-separated lists: FROM funds f, holdings h."""
    found = []
    for m in re.finditer(r"(?i)\b(from|join)\s+", sql):
        rest = sql[m.end():]
        end = CLAUSE_END.search(rest)
        clause = rest[:end.start()] if end else rest
        if m.group(1).lower() == "join":
            clause = clause.split(",")[0]
        for part in clause.split(","):
            name = re.match(r"\s*([a-z_][a-z0-9_]*)", part, re.I)
            if name and not part.strip().startswith("("):
                found.append(name.group(1))
    return found


def check_sql(sql, allowed_tables):
    problems = []
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        problems.append("more than one statement")
    if not re.match(r"(?is)^\s*(select|with)\b", s):
        problems.append("not a SELECT query")
    if FORBIDDEN.search(s):
        problems.append(f"forbidden keyword: {FORBIDDEN.search(s).group(0)}")
    ctes = {c.lower() for c in re.findall(r"(?i)(?:\bwith|,)\s*([a-z_][a-z0-9_]*)\s+as\s*\(", s)}  # WITH t AS (...)
    for t in tables_in(s):
        if t.lower() not in allowed_tables and t.lower() not in ctes:
            problems.append(f"table not allowed: {t}")
    return problems, s


def run_sql(sql, db="data/am/harbourline.sqlite", allowed_tables=None, max_rows=200):
    allowed = allowed_tables or {"funds", "securities", "holdings", "nav", "benchmark_returns",
                                 "issuer_esg", "transactions"}
    problems, s = check_sql(sql, allowed)
    if problems:
        return {"error": "; ".join(problems)}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)          # the database cannot be changed

    def authorise(action, arg1, arg2, dbname, source):                 # the database refuses other tables too
        if action == sqlite3.SQLITE_READ and arg1.lower() not in allowed:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    con.set_authorizer(authorise)
    deadline = time.monotonic() + 10                                   # no query may run longer than 10 s
    con.set_progress_handler(lambda: time.monotonic() > deadline, 10_000)
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
