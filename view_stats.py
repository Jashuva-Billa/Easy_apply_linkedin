# -*- coding: utf-8 -*-
"""Simple Application Stats Viewer"""

import duckdb
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

DB_PATH = 'data/bot_data.duckdb'

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run the bot (python main.py) first to record applications.")
        return
    con = duckdb.connect(DB_PATH, read_only=True)
    
    print("=" * 80)
    print("JOB APPLICATION TRACKING SUMMARY")
    print("=" * 80)
    print()
    
    # Overall Statistics
    print("OVERALL STATISTICS")
    print("-" * 80)
    stats = con.execute("""
        SELECT 
            COUNT(*) as total_applications,
            SUM(CASE WHEN user_submitted THEN 1 ELSE 0 END) as user_confirmations,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_submissions,
            SUM(CASE WHEN user_skipped THEN 1 ELSE 0 END) as user_skips,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            ROUND(AVG(duration_seconds), 2) as avg_duration
        FROM applications
    """).fetchone()
    
    print(f"  Total Applications Started:    {stats[0]}")
    print(f"  User Clicked 'Submit Now':     {stats[1]}")
    print(f"  Successfully Submitted:        {stats[2]}")
    print(f"  User Clicked 'Skip':           {stats[3]}")
    print(f"  Failed Submissions:            {stats[4]}")
    if stats[5]:
        print(f"  Average Duration:              {stats[5]}s")
    print()
    
    # Success Rate
    if stats[1] and stats[1] > 0:
        conversion_rate = round(100.0 * stats[2] / stats[1], 1)
        print(f"  Conversion Rate (Submit Now -> Success): {conversion_rate}%")
        print()
    
    # Recent Applications
    print("RECENT APPLICATIONS (Last 10)")
    print("-" * 80)
    recent = con.execute("""
        SELECT 
            DATE(started_at) as date,
            job_title,
            company,
            status,
            duration_seconds
        FROM applications
        WHERE started_at IS NOT NULL
        ORDER BY started_at DESC
        LIMIT 10
    """).fetchdf()
    
    if len(recent) > 0:
        print(recent.to_string(index=False))
    else:
        print("  No applications yet.")
    print()
    
    # Daily Statistics  
    print("DAILY BREAKDOWN (Last 7 Days)")
    print("-" * 80)
    daily = con.execute("""
        SELECT 
            DATE(started_at) as date,
            COUNT(*) as total,
            SUM(CASE WHEN user_submitted THEN 1 ELSE 0 END) as confirmed,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as submitted,
            SUM(CASE WHEN user_skipped THEN 1 ELSE 0 END) as skipped
        FROM applications
        WHERE started_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(started_at)
        ORDER BY date DESC
    """).fetchdf()
    
    if len(daily) > 0:
        print(daily.to_string(index=False))
    else:
        print("  No applications in last 7 days.")
    print()
    
    # Top Companies
    print("TOP COMPANIES (By Application Count)")
    print("-" * 80)
    companies = con.execute("""
        SELECT 
            company,
            COUNT(*) as applications,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
        FROM applications
        WHERE company IS NOT NULL AND company != 'Unknown'
        GROUP BY company
        ORDER BY applications DESC
        LIMIT 10
    """).fetchdf()
    
    if len(companies) > 0:
        print(companies.to_string(index=False))
    else:
        print("  No company data yet.")
    print()
    
    # Stats by Candidate
    print("BY CANDIDATE")
    print("-" * 80)
    by_candidate = con.execute("""
        SELECT 
            candidate_id,
            COUNT(*) as total,
            SUM(CASE WHEN user_submitted THEN 1 ELSE 0 END) as submitted,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
        FROM applications
        GROUP BY candidate_id
        ORDER BY total DESC
    """).fetchdf()
    
    if len(by_candidate) > 0:
        print(by_candidate.to_string(index=False))
    else:
        print("  No candidate data yet.")
    print()
    
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print("For more queries, see QUERIES.py")
    print("=" * 80)
    
    con.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the bot has run at least once to create the database.")
        import sys
        sys.exit(1)
