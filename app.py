# src/api/app.py

from fastapi import FastAPI, HTTPException

from src.schemas.portal_schemas import (
    SupplierPayload,
    SupplierValidationResponse,
)
from src.core.portal_validation import (
    validate_portal_fields_for_supplier,
)
from src.helpers.bq_storage import write_portal_field_results


app = FastAPI(
    title="Portal Field Validation API",
    description="Validates portal fields for a supplier using ValidationEngine and writes results to BigQuery.",
    version="1.0.0",
)


@app.post(
    "/validate-portal-fields",
    response_model=SupplierValidationResponse,
    tags=["portal_validation"],
    summary="Validate portal fields and write results to BigQuery",
)
def validate_portal_fields(payload: SupplierPayload):
    """
    - Validates incoming portal fields for a supplier using ValidationEngine.
    - Writes one row per field to BigQuery.
    - Returns field-level validation results (visible in Swagger).
    """
    # 1) run validation
    response = validate_portal_fields_for_supplier(
        supplier_id=payload.supplier_id,
        portal_fields=payload.fields,
    )

    # 2) write to BigQuery
    try:
        write_portal_field_results(
            supplier_id=payload.supplier_id,
            results=response.results,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"BigQuery insert failed: {exc}")

    # 3) return response
    return response
