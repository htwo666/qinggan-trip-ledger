#!/usr/bin/env python3
"""Run a SQL file against Supabase Postgres via pooler (pg8000).
Password taken from env SUPA_DB_PW so it never lands in the repo."""
import os, ssl, sys, re
import pg8000.native

REF  = "cxvwynfwoppyzjopzpkz"
HOST = "aws-0-ap-south-1.pooler.supabase.com"
PORT = 5432
PW   = os.environ.get("SUPA_DB_PW")
if not PW:
    sys.exit("ERROR: set SUPA_DB_PW env var")

sql_path = sys.argv[1] if len(sys.argv) > 1 else "supabase/schema.sql"
sql = open(sql_path, encoding="utf-8").read()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = pg8000.native.Connection(
    user=f"postgres.{REF}", password=PW, host=HOST, port=PORT,
    database="postgres", ssl_context=ctx, timeout=60,
)
print(f"connected -> {HOST}:{PORT}")

# split on ';' at line ends, but keep $$ ... $$ bodies intact
stmts, buf, in_dollar = [], [], False
for line in sql.splitlines():
    if line.count("$$") % 2 == 1:
        in_dollar = not in_dollar
    buf.append(line)
    if not in_dollar and line.rstrip().endswith(";"):
        chunk = "\n".join(buf).strip()
        if chunk and not re.fullmatch(r"(--.*\n?)*", chunk):
            stmts.append(chunk)
        buf = []
if buf:
    tail = "\n".join(buf).strip()
    if tail:
        stmts.append(tail)

ok = fail = 0
for i, s in enumerate(stmts, 1):
    label = " ".join(
        l for l in s.splitlines() if l.strip() and not l.strip().startswith("--")
    )[:70]
    try:
        conn.run(s)
        ok += 1
        print(f"  [{i:02d}] OK   {label}")
    except Exception as e:
        fail += 1
        print(f"  [{i:02d}] FAIL {label}\n        -> {str(e)[:220]}")

print(f"\nDone: {ok} ok, {fail} failed")
conn.close()
sys.exit(1 if fail else 0)
