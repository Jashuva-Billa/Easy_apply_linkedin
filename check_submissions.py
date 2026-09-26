# Quick check: How many applications submitted by each candidate
import os
import sys
import duckdb

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DB_PATH = 'data/bot_data.duckdb'

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}. Run the bot (python main.py) first to record applications.")
    sys.exit(0)

try:
    con = duckdb.connect(DB_PATH, read_only=True)
    result = con.execute("""
        SELECT 
            candidate_id as Name,
            SUM(CASE WHEN user_submitted THEN 1 ELSE 0 END) as Submitted
        FROM applications
        GROUP BY candidate_id
        ORDER BY Submitted DESC
    """).fetchdf()
    if len(result) > 0:
        print(result.to_string(index=False))
    else:
        print("No submissions recorded yet.")
    con.close()
except Exception as e:
    print(f"Error querying submissions: {e}")
