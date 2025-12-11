# src/schemas/validation_schemas.py
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

RuleStatus = Literal["PASS", "FAIL", "WARNING", "SKIP"]
class FlagExpectation(BaseModel):
    field: str
    expected: bool


class FieldRef(BaseModel):
    source: Literal["portal", "doc"]
    field: str
    doc_type: Optional[str] = None  # required when source == "doc"


class PortalFieldValidation(BaseModel):
    type: Literal["string", "number", "date", "boolean"] = "string"
    required: bool = True
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    description: Optional[str] = None


class CrossSourceRule(BaseModel):
    id: str
    description: str
    severity: Literal["error", "warning"] = "error"
    rule_type: Literal[
        "equality",
        "in_set",
        "regex",
        "date_within_year",
        "page_count_between",
        "flags_match",
    ]
    left: Optional[FieldRef] = None
    right: Optional[FieldRef] = None
    target: Optional[FieldRef] = None

    # rule-specific config
    allowed_values: Optional[List[str]] = None
    regex: Optional[str] = None
    year_delta: Optional[int] = None
    min_pages: Optional[int] = None
    max_pages: Optional[int] = None
    flags: Optional[List[FlagExpectation]] = None


class ValidationConfig(BaseModel):
    portal_field_validations: Dict[str, PortalFieldValidation] = Field(default_factory=dict)
    cross_source_rules: List[CrossSourceRule] = Field(default_factory=list)


class RuleResult(BaseModel):
    rule_id: str
    description: str
    status: RuleStatus
    severity: Literal["error", "warning"]
    message: str
    context: Dict[str, str] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    summary_status: RuleStatus
    results: List[RuleResult]
