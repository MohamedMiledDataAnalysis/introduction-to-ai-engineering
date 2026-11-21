# Exercise 11.2 - A read-only connection
# Run from the root of the repository:  python chapters/ch11/python/solutions/ex11_2_read_only.py

import sqlite3
con = sqlite3.connect("file:data/am/harbourline.sqlite?mode=ro", uri=True)
try:
    con.execute("DELETE FROM issuer_esg")
except sqlite3.OperationalError as err:
    print("refused:", err)
