#!/usr/bin/env python3
"""
Nightly F-UJI FAIR assessment for EDP metadata records.
Reads uuids from main_page_geonetworkmetadata, calls F-UJI, upserts scores
and stores the full API response in full_result (jsonb).
"""
import os
import re
import sys
import time
from datetime import datetime, timezone

import psycopg2
import requests
from psycopg2.extras import Json, RealDictCursor

FUJI_API_URL = os.environ.get("FUJI_API_URL", "http://10.8.244.43:1071/fuji/api/v1")
FUJI_USER = os.environ.get("FUJI_API_USER", "marvel")
FUJI_PASSWORD = os.environ.get("FUJI_API_PASSWORD", "")
EDP_DISCOVERY_BASE = os.environ.get(
    "EDP_DISCOVERY_URL", "https://edp-portal.eurac.edu/discovery/"
).rstrip("/") + "/"

DB = {
    "host": os.environ["DB_HOST"],
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

REQUEST_TIMEOUT = int(os.environ.get("FUJI_TIMEOUT", "180"))
SLEEP_BETWEEN = float(os.environ.get("FUJI_SLEEP", "2"))
ONLY_MISSING = os.environ.get("FUJI_ONLY_MISSING", "true").lower() in ("1", "true", "yes")
LIMIT = int(os.environ["FUJI_LIMIT"]) if os.environ.get("FUJI_LIMIT") else None

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def discovery_url(uuid: str) -> str:
    return f"{EDP_DISCOVERY_BASE}{uuid}"


def maturity_label(value):
    labels = {0: "incomplete", 1: "initial", 2: "moderate", 3: "advanced"}
    return labels.get(round(float(value or 0)), "incomplete")


def parse_scores(payload: dict) -> dict:
    summary = payload["summary"]
    pct = summary["score_percent"]
    earned = summary["score_earned"]
    total = summary["score_total"]
    maturity = summary["maturity"]

    return {
        "score_overall": pct.get("FAIR"),
        "score_f": pct.get("F"),
        "score_a": pct.get("A"),
        "score_i": pct.get("I"),
        "score_r": pct.get("R"),
        "earned_f": earned.get("F"),
        "earned_a": earned.get("A"),
        "earned_i": earned.get("I"),
        "earned_r": earned.get("R"),
        "total_f": total.get("F"),
        "total_a": total.get("A"),
        "total_i": total.get("I"),
        "total_r": total.get("R"),
        "maturity_f": round(maturity.get("F", 0)),
        "maturity_a": round(maturity.get("A", 0)),
        "maturity_i": round(maturity.get("I", 0)),
        "maturity_r": round(maturity.get("R", 0)),
        "maturity_overall": maturity.get("FAIR"),
        "metric_version": str(payload.get("metric_version", "")),
        "fuji_test_id": payload.get("test_id"),
        "assessed_at": payload.get("end_timestamp"),
    }


def evaluate(uuid: str):
    """Call F-UJI and return (parsed_scores, full_response)."""
    body = {
        "object_identifier": discovery_url(uuid),
        "test_debug": False,
        "use_datacite": True,
        "use_github": False,
        "metric_version": "metrics_v0.8",
    }
    r = requests.post(
        f"{FUJI_API_URL.rstrip('/')}/evaluate",
        json=body,
        auth=(FUJI_USER, FUJI_PASSWORD),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    payload = r.json()
    return parse_scores(payload), payload


def fetch_uuids(conn):
    sql = """
        SELECT m.uuid
        FROM main_page_geonetworkmetadata m
        WHERE m.uuid ~ '^[0-9a-fA-F-]{36}$'
    """
    if ONLY_MISSING:
        sql += """
          AND NOT EXISTS (
            SELECT 1 FROM main_page_fairscore f WHERE f.uuid = m.uuid
          )
        """
    sql += " ORDER BY m.title"
    if LIMIT:
        sql += f" LIMIT {int(LIMIT)}"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return [row["uuid"] for row in cur.fetchall()]


def upsert_score(conn, uuid: str, object_identifier: str, scores: dict, full_result: dict):
    sql = """
        INSERT INTO main_page_fairscore (
            uuid, object_identifier,
            score_overall, score_f, score_a, score_i, score_r,
            earned_f, earned_a, earned_i, earned_r,
            total_f, total_a, total_i, total_r,
            maturity_f, maturity_a, maturity_i, maturity_r, maturity_overall,
            metric_version, fuji_test_id, assessed_at, updated_at,
            full_result
        ) VALUES (
            %(uuid)s, %(object_identifier)s,
            %(score_overall)s, %(score_f)s, %(score_a)s, %(score_i)s, %(score_r)s,
            %(earned_f)s, %(earned_a)s, %(earned_i)s, %(earned_r)s,
            %(total_f)s, %(total_a)s, %(total_i)s, %(total_r)s,
            %(maturity_f)s, %(maturity_a)s, %(maturity_i)s, %(maturity_r)s, %(maturity_overall)s,
            %(metric_version)s, %(fuji_test_id)s, %(assessed_at)s, %(updated_at)s,
            %(full_result)s
        )
        ON CONFLICT (uuid) DO UPDATE SET
            object_identifier = EXCLUDED.object_identifier,
            score_overall = EXCLUDED.score_overall,
            score_f = EXCLUDED.score_f,
            score_a = EXCLUDED.score_a,
            score_i = EXCLUDED.score_i,
            score_r = EXCLUDED.score_r,
            earned_f = EXCLUDED.earned_f,
            earned_a = EXCLUDED.earned_a,
            earned_i = EXCLUDED.earned_i,
            earned_r = EXCLUDED.earned_r,
            total_f = EXCLUDED.total_f,
            total_a = EXCLUDED.total_a,
            total_i = EXCLUDED.total_i,
            total_r = EXCLUDED.total_r,
            maturity_f = EXCLUDED.maturity_f,
            maturity_a = EXCLUDED.maturity_a,
            maturity_i = EXCLUDED.maturity_i,
            maturity_r = EXCLUDED.maturity_r,
            maturity_overall = EXCLUDED.maturity_overall,
            metric_version = EXCLUDED.metric_version,
            fuji_test_id = EXCLUDED.fuji_test_id,
            assessed_at = EXCLUDED.assessed_at,
            updated_at = EXCLUDED.updated_at,
            full_result = EXCLUDED.full_result
    """
    data = {
        "uuid": uuid,
        "object_identifier": object_identifier,
        "updated_at": datetime.now(timezone.utc),
        "full_result": Json(full_result),
        **scores,
    }
    with conn.cursor() as cur:
        cur.execute(sql, data)


def main():
    if not FUJI_USER or not FUJI_PASSWORD:
        print("ERROR: set FUJI_API_USER and FUJI_API_PASSWORD", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(**DB)
    conn.autocommit = False

    uuids = fetch_uuids(conn)
    print(f"Records to assess: {len(uuids)}")

    ok, fail = 0, 0
    for i, uuid in enumerate(uuids, 1):
        if not UUID_RE.match(uuid):
            continue
        try:
            print(f"[{i}/{len(uuids)}] {uuid} ...", flush=True)
            scores, full_result = evaluate(uuid)
            upsert_score(conn, uuid, discovery_url(uuid), scores, full_result)
            conn.commit()
            ok += 1
            print(f"  FAIR={scores['score_overall']}%", flush=True)
        except Exception as exc:
            conn.rollback()
            fail += 1
            print(f"  FAILED: {exc}", file=sys.stderr)
        time.sleep(SLEEP_BETWEEN)

    conn.close()
    print(f"Done. success={ok} failed={fail}")
    sys.exit(1 if fail and not ok else 0)


if __name__ == "__main__":
    main()
