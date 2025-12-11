# src/core/portal_validation.py

from typing import Any, Dict, List, Optional

from src.core.validation_engine import ValidationEngine
from src.schemas.validation_schemas import ValidationReport
from src.schemas.portal_schemas import (
    FieldValidationResult,
    SupplierValidationResponse,
)
import os
PORTAL_CONFIG_PATH = os.getenv(
    "PORTAL_VALIDATION_CONFIG_PATH",
    "configs/portal_validation_config.json",
)


# Load once at startup
ENGINE = ValidationEngine.from_json_file(PORTAL_CONFIG_PATH)


def _failure_reason_from_rule_id(rule_id: str) -> str:
    """
    Map ValidationEngine rule IDs to short failure reasons
    that you can store in BigQuery.
    """
    prefix = rule_id.split("::", 1)[0]
    if prefix == "PORTAL_FIELD_REQUIRED":
        return "MISSING_REQUIRED"
    if prefix == "PORTAL_FIELD_PATTERN":
        return "PATTERN_MISMATCH"
    if prefix == "PORTAL_FIELD_IN_SET":
        return "INVALID_VALUE"
    if prefix == "PORTAL_FIELD_MIN_LEN":
        return "MIN_LENGTH"
    if prefix == "PORTAL_FIELD_MAX_LEN":
        return "MAX_LENGTH"
    return "GENERIC_FAIL"


def portal_report_to_field_results(
    report: ValidationReport, portal_json: Dict[str, Any]
) -> List[FieldValidationResult]:
    """
    Take ValidationReport from ValidationEngine and convert it to
    one FieldValidationResult per *portal* field.

    We only care about portal rules whose rule_id starts with 'PORTAL_FIELD_'.
    Cross-source rules are ignored here.
    """
    by_field: Dict[str, FieldValidationResult] = {}

    for rule_res in report.results:
        if not rule_res.rule_id.startswith("PORTAL_FIELD_"):
            # skip cross-source rules; this endpoint is portal-only
            continue

        # rule_id looks like: PORTAL_FIELD_XXX::<field_name>
        try:
            _, field_name = rule_res.rule_id.split("::", 1)
        except ValueError:
            # unexpected format; skip to be safe
            continue

        raw_val = portal_json.get(field_name)
        value_str: Optional[str] = None if raw_val is None else str(raw_val)

        if rule_res.status == "PASS":
            is_valid = True
            failure_reason = None
        else:
            is_valid = False
            failure_reason = _failure_reason_from_rule_id(rule_res.rule_id)

        by_field[field_name] = FieldValidationResult(
            field_name=field_name,
            value=value_str,
            is_valid=is_valid,
            failure_reason=failure_reason,
        )

    return list(by_field.values())


def validate_portal_fields_for_supplier(
    supplier_id: str, portal_fields: Dict[str, Any]
) -> SupplierValidationResponse:
    """
    High-level function used by the API:
    - runs ValidationEngine (portal-only)
    - converts to field-level results
    """
    report = ENGINE.validate(
        portal_json=portal_fields,
        docs_by_type={},  # portal-only scenario
    )

    field_results = portal_report_to_field_results(report, portal_fields)

    return SupplierValidationResponse(
        supplier_id=supplier_id,
        results=field_results,
    )



# # src/core/portal_validation_runner.py
# import argparse
# import json
# from pathlib import Path
# from typing import Dict, Any

# from src.core.validation_engine import ValidationEngine


# def load_portal_json(path: Path) -> Dict[str, Any]:
#     with path.open("r", encoding="utf-8") as f:
#         return json.load(f)


# def run_for_vendor(
#     engine: ValidationEngine,
#     portal_file: Path,
#     output_root: Path,
# ) -> None:
#     vendor_id = portal_file.stem  # e.g. vendor_123
#     portal_json = load_portal_json(portal_file)

#     # portal-only => docs_by_type is empty
#     report = engine.validate(portal_json=portal_json, docs_by_type={})

#     output_root.mkdir(parents=True, exist_ok=True)
#     out_path = output_root / f"{vendor_id}_portal_report.json"
#     out_path.write_text(
#         report.model_dump_json(indent=2, ensure_ascii=False),
#         encoding="utf-8",
#     )
#     print(f"[PORTAL] {vendor_id}: {report.summary_status} -> {out_path}")


# def main() -> None:
#     parser = argparse.ArgumentParser(description="Portal-only validation")
#     parser.add_argument(
#         "--config",
#         type=Path,
#         default=Path("configs/portal_validation_config.json"),
#         help="Path to portal validation config JSON",
#     )
#     parser.add_argument(
#         "--portal-root",
#         type=Path,
#         default=Path("data/portal"),
#         help="Folder containing portal vendor JSON files",
#     )
#     parser.add_argument(
#         "--vendor-id",
#         type=str,
#         default=None,
#         help="Optional vendor ID to validate (e.g. vendor_123). If omitted, run for all.",
#     )
#     parser.add_argument(
#         "--output-root",
#         type=Path,
#         default=Path("outputs/portal_validation"),
#         help="Folder where validation reports will be written",
#     )

#     args = parser.parse_args()

#     engine = ValidationEngine.from_json_file(args.config)

#     if args.vendor_id:
#         portal_file = args.portal_root / f"{args.vendor_id}.json"
#         if not portal_file.exists():
#             raise SystemExit(f"Portal file not found: {portal_file}")
#         run_for_vendor(engine, portal_file, args.output_root)
#     else:
#         for portal_file in sorted(args.portal_root.glob("*.json")):
#             run_for_vendor(engine, portal_file, args.output_root)


# if __name__ == "__main__":
#     main()
