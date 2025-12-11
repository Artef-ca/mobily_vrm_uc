from typing import Any, List, Optional
from pydantic import BaseModel, Field


class RuleMatch(BaseModel):
    success: bool = Field(..., description="Did this rule pass?")
    score: Optional[float] = Field(
        None,
        description="Similarity score when applicable (0–1)."
    )
    left_value: Any = Field(None, description="Left compared value")
    right_value: Any = Field(None, description="Right compared value")
    message: str = Field(..., description="Human-readable explanation")


class RuleResult(BaseModel):
    rule_id: str
    description: str
    severity: str  # "error" | "warning"
    status: str    # "pass" | "fail" | "error"
    match: RuleMatch


class ValidationSummary(BaseModel):
    total_rules: int
    errors: int
    warnings: int


class ValidationResponse(BaseModel):
    summary: ValidationSummary
    results: List[RuleResult]
