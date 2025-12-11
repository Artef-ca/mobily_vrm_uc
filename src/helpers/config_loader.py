from __future__ import annotations
from pathlib import Path
import yaml
import json
from typing import Dict, Any

from src.schemas.validation_schemas import ValidationConfig


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_validation_config(
    path: Path | str = PROJECT_ROOT / "configs" / "validation_rules.yaml",
) -> ValidationConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ValidationConfig(**raw)


def load_vendor_context_from_folders(
    vendor_id: str,
    ocr_root: Path,
    master_root: Path,
) -> Dict[str, Dict[str, Any]]:
    """
    Example layout:
      data/ocr_docs/{vendor_id}/CR.json
      data/ocr_docs/{vendor_id}/VAT.json
      data/ocr_docs/{vendor_id}/CoC.json
      data/master_data/{vendor_id}/vendor_master.json
    These file names are just examples – adjust to your real naming.
    """

    context: Dict[str, Dict[str, Any]] = {}

    # Vendor master (Oracle / GCP bucket data)
    vendor_master_path = master_root / vendor_id / "vendor_master.json"
    if vendor_master_path.exists():
        with vendor_master_path.open("r", encoding="utf-8") as f:
            context["oracle.vendor"] = json.load(f)

    # OCR docs (per document type)
    ocr_vendor_dir = ocr_root / vendor_id
    if ocr_vendor_dir.exists():
        for p in ocr_vendor_dir.glob("*.json"):
            doc_type = p.stem  # e.g. "CR", "VAT", "CoC", "NDA"
            with p.open("r", encoding="utf-8") as f:
                context[f"ocr.{doc_type}"] = json.load(f)

    return context
