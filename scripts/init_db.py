"""
Quick sanity check that the app can connect to MySQL and see the tables
created by db/ddl.sql + db/seed.sql. Does NOT create or alter any schema —
DDL is DBA-owned (see db/ddl.sql).

Usage: python scripts/init_db.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models import Hospital, Staff, Patient

app = create_app()

with app.app_context():
    try:
        hospital_count = db.session.query(Hospital).count()
        staff_count = db.session.query(Staff).count()
        patient_count = db.session.query(Patient).count()
        print("Connected to MySQL successfully.")
        print(f"  hospitals: {hospital_count}")
        print(f"  staff:     {staff_count}")
        print(f"  patients:  {patient_count}")
        if hospital_count == 0:
            print("\nNo rows found — did you run db/ddl.sql and db/seed.sql against your MySQL instance?")
    except Exception as exc:
        print(f"Could not query the database: {exc}")
        print("Check .env MYSQL_* settings and confirm db/ddl.sql has been applied.")
        sys.exit(1)
