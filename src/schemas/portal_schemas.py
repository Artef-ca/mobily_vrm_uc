# src/schemas/api_schemas.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SupplierPayload(BaseModel):
    supplier_id: str = Field(..., description="Vendor/supplier identifier")
    fields: Dict[str, Any] = Field(
        ..., description="Key-value mapping of portal fields to their values"
    )


class FieldValidationResult(BaseModel):
    field_name: str
    value: Optional[str]
    is_valid: bool
    failure_reason: Optional[str] = None  # e.g. 'MISSING_REQUIRED', 'PATTERN_MISMATCH', 'INVALID_VALUE'


class SupplierValidationResponse(BaseModel):
    supplier_id: str
    results: List[FieldValidationResult]
