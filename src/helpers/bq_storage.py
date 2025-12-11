# src/helpers/bq_storage.py

import os
from datetime import datetime
from typing import List

from google.cloud import bigquery

from src.schemas.portal_schemas import FieldValidationResult


BQ_PROJECT = os.getenv("BQ_PROJECT")
BQ_DATASET = os.getenv("BQ_DATASET", "vrm_validation")
BQ_TABLE = os.getenv("BQ_TABLE", "portal_field_validation")


def get_bq_client() -> bigquery.Client:
    """
    Returns a BigQuery client using the project from env.
    """
    if not BQ_PROJECT:
        raise RuntimeError("BQ_PROJECT env variable must be set")
    return bigquery.Client(project=BQ_PROJECT)


def write_portal_field_results(
    supplier_id: str,
    results: List[FieldValidationResult],
) -> None:
    """
    Writes one row per portal field into BigQuery.

    Expected table schema:
        supplier_id: STRING
        field_name: STRING
        field_value: STRING
        is_valid: BOOL
        failure_reason: STRING
        created_at: TIMESTAMP
    """
    client = get_bq_client()
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    now = datetime.utcnow().isoformat()

    rows_to_insert = [
        {
            "supplier_id": supplier_id,
            "field_name": r.field_name,
            "field_value": r.value,
            "is_valid": r.is_valid,
            "failure_reason": r.failure_reason,
            "created_at": now,
        }
        for r in results
    ]

    errors = client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        # let caller see the error; you can also log here
        raise RuntimeError(f"Failed to insert into BigQuery: {errors}")
