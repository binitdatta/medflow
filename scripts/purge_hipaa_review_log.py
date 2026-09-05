"""
Retention helper for llm_hipaa_review_log. Deletes only rows that have
already been marked reviewed=TRUE and are older than --days -- unreviewed
rows are never touched, regardless of age, since purging something no one
has actually reviewed defeats the point of the table.

This does NOT upload anything to S3 -- that's your infrastructure to wire
up. The obvious place to add it is marked below with a comment: export the
rows this script is about to delete (e.g. via `mysqldump` with a WHERE
clause matching the same criteria, or a SELECT ... INTO OUTFILE, or a
Python export loop) to your backup destination BEFORE the DELETE runs.

Usage:
    python scripts/purge_hipaa_review_log.py --days 90
    python scripts/purge_hipaa_review_log.py --days 90 --dry-run
"""
import argparse
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.llm_hipaa_review import LlmHipaaReviewLog

app = create_app()

parser = argparse.ArgumentParser(description="Purge reviewed HIPAA review log rows older than N days.")
parser.add_argument("--days", type=int, default=90, help="Delete reviewed rows older than this many days (default 90).")
parser.add_argument("--dry-run", action="store_true", help="Report what would be deleted without deleting anything.")
args = parser.parse_args()

with app.app_context():
    cutoff = datetime.utcnow() - timedelta(days=args.days)

    query = LlmHipaaReviewLog.query.filter(
        LlmHipaaReviewLog.reviewed == True,  # noqa: E712
        LlmHipaaReviewLog.created_at < cutoff,
    )
    count = query.count()

    print(f"Found {count} reviewed row(s) older than {args.days} days (before {cutoff.isoformat()}).")

    if count == 0:
        sys.exit(0)

    if args.dry_run:
        print("--dry-run set: not deleting anything.")
        sys.exit(0)

    # -----------------------------------------------------------------
    # TODO: export `query`'s rows to your backup destination (S3, etc.)
    # HERE, before the delete below runs. e.g.:
    #
    #   import boto3, json
    #   rows = [r.to_dict(include_body=True) for r in query.all()]
    #   boto3.client("s3").put_object(
    #       Bucket="your-bucket",
    #       Key=f"medflow/hipaa-review-archive/{datetime.utcnow():%Y%m%d}.json",
    #       Body=json.dumps(rows),
    #   )
    # -----------------------------------------------------------------

    deleted = query.delete(synchronize_session=False)
    db.session.commit()
    print(f"Deleted {deleted} row(s).")