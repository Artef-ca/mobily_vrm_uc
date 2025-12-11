from typing import Dict, Any
from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """
    Incoming payload for the validation endpoint.

    documents:
      key   -> logical source name ("vendor_input", "nda", "moc_certificate"...)
      value -> JSON extracted from OCR or other sources
    """
    documents: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Mapping: source_name -> document JSON content"
    )
