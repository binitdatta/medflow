"""
Structured JSON logging to stdout, separate from the DB-backed audit trail
in models.system_log. This exists specifically for production log
centralization: a log shipper (FluentD, Fluent Bit, Filebeat, Vector, etc.)
tails the container's stdout and forwards each line to Elasticsearch/ELK,
Splunk, Datadog, or similar -- no code here talks to those systems directly,
it just emits well-formed single-line JSON so any of them can ingest it.

Two loggers:
  http_logger  -- one line per inbound HTTP request (see services/logging_service.py)
  llm_logger   -- one line per Anthropic API call, full request/response included

Why not just log the DB write? Two independent sinks on purpose: the MySQL
tables (http_call_log / llm_call_log) are queryable from the app itself and
subject to the app's own retention/backup policy; the stdout stream is for
infrastructure-level tooling that has nothing to do with the app's database
and needs to keep working even if MySQL is down.

Log rotation / retention for the stdout stream is the log shipper's/
container runtime's job (e.g. Docker's log-driver options, or whatever
FluentD/ELK retention policy you configure) -- this module has no rotation
logic of its own by design.
"""
import json
import logging
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }
        if isinstance(record.msg, dict):
            payload.update(record.msg)
        else:
            payload["message"] = record.getMessage()
        try:
            return json.dumps(payload, default=str)
        except (TypeError, ValueError):
            # Never let a logging call raise -- fall back to a safe, partial line
            # rather than losing the log entry (or worse, crashing the request).
            return json.dumps({
                "timestamp": payload["timestamp"],
                "level": payload["level"],
                "logger": payload["logger"],
                "message": "log payload was not JSON-serializable",
            })


def _build_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # don't also pass through Flask's default handler and double-print
    return logger


http_logger = _build_logger("medflow.http")
llm_logger = _build_logger("medflow.llm")