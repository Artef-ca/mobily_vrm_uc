# src/core/validation_engine.py
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from src.schemas.validation_schemas import (
    ValidationConfig,
    ValidationReport,
    RuleResult,
    CrossSourceRule,
    PortalFieldValidation,
    RuleStatus,
    FieldRef,
)


class ValidationEngine:
    def __init__(self, config: ValidationConfig):
        self.config = config

    # --------- construction ---------

    @classmethod
    def from_json_file(cls, path: str | Path) -> "ValidationEngine":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = ValidationConfig.model_validate(data)
        return cls(cfg)

    # --------- public API ---------

    def validate(
        self,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> ValidationReport:
        """
        portal_json: JSON from registration portal (one vendor)
        docs_by_type: mapping of doc_type -> extracted JSON (one vendor)
                      each doc JSON should either have:
                        - {"doc_type": "nda", "fields": {...}}
                      or we treat the whole JSON as the fields dict.
        """
        results: list[RuleResult] = []

        # 1) portal-only checks (format/required/etc.)
        for field_name, field_cfg in self.config.portal_field_validations.items():
            res = self._validate_portal_field(field_name, field_cfg, portal_json)
            if res is not None:
                results.append(res)

        # 2) cross-source rules (portal vs docs / doc vs doc)
        for rule in self.config.cross_source_rules:
            res = self._apply_rule(rule, portal_json, docs_by_type)
            results.append(res)


        summary_status = self._aggregate_status(results)
        return ValidationReport(summary_status=summary_status, results=results)

    # --------- helpers ---------

    def _aggregate_status(self, results: list[RuleResult]) -> RuleStatus:
        has_fail = any(r.status == "FAIL" for r in results)
        has_warning = any(r.status == "WARNING" for r in results)
        if has_fail:
            return "FAIL"
        if has_warning:
            return "WARNING"
        return "PASS"

    # ----- portal single-field validation -----

    def _validate_portal_field(
        self,
        field_name: str,
        cfg: PortalFieldValidation,
        portal_json: Dict[str, Any],
    ) -> RuleResult | None:
        raw_value = portal_json.get(field_name)

        if raw_value in (None, ""):
            if cfg.required:
                return RuleResult(
                    rule_id=f"PORTAL_FIELD_REQUIRED::{field_name}",
                    description=f"{field_name} is required",
                    severity="error",
                    status="FAIL",
                    message=f"Field '{field_name}' is missing or empty.",
                )
            return None  # optional & empty => no result

        value_str = str(raw_value)

        # regex pattern
        if cfg.pattern:
            if not re.match(cfg.pattern, value_str):
                return RuleResult(
                    rule_id=f"PORTAL_FIELD_PATTERN::{field_name}",
                    description=f"{field_name} must match pattern",
                    severity="error",
                    status="FAIL",
                    message=f"Field '{field_name}' has invalid format: {value_str!r}",
                )

        # allowed values
        if cfg.allowed_values:
            if value_str not in cfg.allowed_values:
                return RuleResult(
                    rule_id=f"PORTAL_FIELD_IN_SET::{field_name}",
                    description=f"{field_name} must be one of allowed values",
                    severity="error",
                    status="FAIL",
                    message=f"Field '{field_name}' has value {value_str!r} not in {cfg.allowed_values}",
                )

        # length checks
        if cfg.min_length is not None and len(value_str) < cfg.min_length:
            return RuleResult(
                rule_id=f"PORTAL_FIELD_MIN_LEN::{field_name}",
                description=f"{field_name} must have at least {cfg.min_length} characters",
                severity="error",
                status="FAIL",
                message=f"Field '{field_name}' is too short",
            )

        if cfg.max_length is not None and len(value_str) > cfg.max_length:
            return RuleResult(
                rule_id=f"PORTAL_FIELD_MAX_LEN::{field_name}",
                description=f"{field_name} must have at most {cfg.max_length} characters",
                severity="error",
                status="FAIL",
                message=f"Field '{field_name}' is too long",
            )

        # if everything is fine, we still return a PASS (nice for debugging)
        return RuleResult(
            rule_id=f"PORTAL_FIELD_OK::{field_name}",
            description=f"{field_name} basic validation",
            severity="warning",
            status="PASS",
            message=f"Field '{field_name}' passed basic validation.",
        )
    

    # ----- cross-source dispatcher -----

    def _apply_rule(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        try:
            if rule.rule_type == "equality":
                return self._rule_equality(rule, portal_json, docs_by_type)
            if rule.rule_type == "in_set":
                return self._rule_in_set(rule, portal_json, docs_by_type)
            if rule.rule_type == "regex":
                return self._rule_regex(rule, portal_json, docs_by_type)
            if rule.rule_type == "date_within_year":
                return self._rule_date_within_year(rule, portal_json, docs_by_type)
            if rule.rule_type == "page_count_between":
                return self._rule_page_count(rule, portal_json, docs_by_type)
            if rule.rule_type == "flags_match":
                return self._rule_flags_match(rule, portal_json, docs_by_type)

            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="SKIP",
                message=f"Unknown rule_type {rule.rule_type!r}",
            )
        except Exception as exc:
            # defensive: never crash the whole run because of one rule
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="FAIL",
                message=f"Exception while applying rule: {exc}",
            )

    # ----- generic helpers -----

    def _resolve_field(
        self,
        ref: FieldRef,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> Tuple[Any, str]:
        if ref.source == "portal":
            return portal_json.get(ref.field), f"portal.{ref.field}"
        if ref.source == "doc":
            if not ref.doc_type:
                raise ValueError("doc_type is required for doc source")
            doc = docs_by_type.get(ref.doc_type, {})
            # allow both {fields: {...}} and flat objects
            fields = doc.get("fields", doc)
            return fields.get(ref.field), f"{ref.doc_type}.{ref.field}"
        raise ValueError(f"Unknown source {ref.source}")

    # ----- rule implementations -----

    def _rule_equality(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.left and rule.right
        left_val, left_path = self._resolve_field(rule.left, portal_json, docs_by_type)
        right_val, right_path = self._resolve_field(rule.right, portal_json, docs_by_type)

        if left_val is None or right_val is None:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="FAIL",
                message=f"Missing values: {left_path}={left_val!r}, {right_path}={right_val!r}",
                context={"left_path": left_path, "right_path": right_path},
            )

        if str(left_val).strip() == str(right_val).strip():
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"Values match for {left_path} and {right_path}",
                context={"left": str(left_val), "right": str(right_val)},
            )

        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"Values differ: {left_path}={left_val!r}, {right_path}={right_val!r}",
            context={"left": str(left_val), "right": str(right_val)},
        )

    def _rule_in_set(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.target and rule.allowed_values
        value, path = self._resolve_field(rule.target, portal_json, docs_by_type)
        if value is None:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="FAIL",
                message=f"Missing value at {path}",
            )

        value_str = str(value)
        if value_str in rule.allowed_values:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"{path} value {value_str!r} is allowed",
            )

        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"{path} value {value_str!r} is not in allowed set {rule.allowed_values}",
        )

    def _rule_regex(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.target and rule.regex
        value, path = self._resolve_field(rule.target, portal_json, docs_by_type)
        value_str = "" if value is None else str(value)

        if re.match(rule.regex, value_str):
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"{path} value matches regex",
            )

        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"{path} value {value_str!r} does not match regex {rule.regex!r}",
        )

    def _rule_date_within_year(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.target
        value, path = self._resolve_field(rule.target, portal_json, docs_by_type)
        if not value:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="FAIL",
                message=f"{path} is missing",
            )

        year_delta = rule.year_delta or 0
        try:
            dt = self._parse_date(str(value))
        except ValueError as exc:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="FAIL",
                message=f"{path} date parse error: {exc}",
            )

        now = datetime.utcnow().date()
        diff_years = abs(now.year - dt.year)
        if diff_years <= year_delta:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"{path} date {dt.isoformat()} is within {year_delta} year(s) of now",
            )

        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"{path} date {dt.isoformat()} is older than {year_delta} year(s)",
        )

    def _parse_date(self, value: str) -> datetime.date:
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unsupported date format {value!r}")

    def _rule_page_count(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.target
        doc_type = rule.target.doc_type
        if not doc_type:
            raise ValueError("page_count_between rule requires target.doc_type")

        doc = docs_by_type.get(doc_type, {})
        pages = doc.get("pages") or doc.get("page_count")

        if isinstance(pages, list):
            page_count = len(pages)
        else:
            page_count = int(pages or 0)

        min_pages = rule.min_pages or 0
        max_pages = rule.max_pages or 10**9

        if min_pages <= page_count <= max_pages:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"{doc_type} has {page_count} pages (within [{min_pages}, {max_pages}])",
            )

        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"{doc_type} has {page_count} pages (expected between {min_pages} and {max_pages})",
        )

    def _rule_flags_match(
        self,
        rule: CrossSourceRule,
        portal_json: Dict[str, Any],
        docs_by_type: Dict[str, Dict[str, Any]],
    ) -> RuleResult:
        assert rule.target and rule.flags
        doc_type = rule.target.doc_type
        if not doc_type:
            raise ValueError("flags_match rule requires target.doc_type")

        doc = docs_by_type.get(doc_type, {})
        fields = doc.get("fields", doc)

        mismatches = []
        for flag in rule.flags:
            fname = flag.field
            expected = flag.expected
            actual = bool(fields.get(fname))
            if actual != expected:
                mismatches.append((fname, expected, actual))

        if not mismatches:
            return RuleResult(
                rule_id=rule.id,
                description=rule.description,
                severity=rule.severity,
                status="PASS",
                message=f"All required flags present for {doc_type}",
            )

        details = ", ".join(
            f"{name}=expected {exp}, got {act}" for name, exp, act in mismatches
        )
        return RuleResult(
            rule_id=rule.id,
            description=rule.description,
            severity=rule.severity,
            status="FAIL",
            message=f"Flag mismatches for {doc_type}: {details}",
        )
