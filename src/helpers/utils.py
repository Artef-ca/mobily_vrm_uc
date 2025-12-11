import os
from pathlib import Path
from typing import Iterable, List, Tuple
import json
import re
from typing import Any, Dict



def list_files_with_suffix(
    root: Path,
    suffixes: Iterable[str],
) -> List[Path]:
    """
    Recursively list all files under `root` that end with any of `suffixes`.

    Example:
        list_files_with_suffix(Path("data"), [".pdf", ".PDF"])
    """
    root = root.resolve()
    suffixes_tuple: Tuple[str, ...] = tuple(suffixes)
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix in suffixes_tuple
    )

def convert_simple_doc(raw_json: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Generic wrapper: takes {pages_count, response}, turns into
    {doc_type, page_count, fields}.
    """
    page_count = raw_json.get("pages_count")
    fields = parse_response_json(raw_json)

    return {
        "doc_type": doc_type,
        "page_count": page_count,
        "fields": fields,
    }

def list_pdfs(root: Path) -> List[Path]:
    """
    Convenience wrapper to recursively list all PDFs under `root`.
    """
    return list_files_with_suffix(root, [".pdf", ".PDF"])


def list_jsons(root: Path, raw_only: bool = False) -> List[Path]:
    """
    Recursively list all JSON files.

    If raw_only=True, only returns files ending with '_raw.json'.
    """
    root = root.resolve()
    all_jsons = sorted(
        p for p in root.rglob("*.json")
        if p.is_file()
    )
    if raw_only:
        all_jsons = [p for p in all_jsons if p.name.endswith("_raw.json")]
    return all_jsons


def parse_response_json(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the `response` field from the raw JSON.
    Handles:
    - response as already-parsed dict
    - response as a JSON string
    - response as a long text with embedded JSON (fallback)
    """
    resp = raw.get("response", "")

    # Already a dict
    if isinstance(resp, dict):
        return resp

    if not isinstance(resp, str):
        return {}

    text = resp.strip()

    # 1) Try direct JSON
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # 2) Fallback: try to extract last {...} from the text
    candidates = []
    for match in re.finditer(r"\{.*?\}", text, flags=re.DOTALL):
        snippet = match.group(0)
        try:
            obj = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            candidates.append(obj)

    if not candidates:
        return {}

    return candidates[-1]

# -------------------------
# MOC / Wathq helpers
# -------------------------

def extract_cr_from_portal(portal_json: Dict[str, Any]) -> str | None:
    """
    Try to extract CR number from the portal JSON.

    Adjust keys based on your real portal schema.
    """
    # Most likely candidates
    candidate_keys = [
        "CR Number",
        "Cr Number",
        "cr_number",
        "crNumber",
        "commercial_registration_number",
        "commercialRegistrationNumber",
    ]

    # 1) Direct top-level keys
    for key in candidate_keys:
        if key in portal_json and portal_json[key]:
            return str(portal_json[key]).strip()

    # 2) Nested under "basic_info" if your portal JSON is structured
    basic_info = portal_json.get("basic_info") or portal_json.get("basicInfo")
    if isinstance(basic_info, dict):
        for key in candidate_keys:
            if key in basic_info and basic_info[key]:
                return str(basic_info[key]).strip()

    # logger.warning("Could not find CR number field in portal JSON.")
    return None


def write_moc_structured_json(
    vendor_id: str,
    structured_docs_root: Path,
    moc_fields: Dict[str, Any],
) -> None:
    """
    Wrap Wathq fields into a structured JSON with doc_type 'moc_certificate'
    and save under extracted_results_structured/<vendor_id>/moc_certificate.json
    """
    vendor_dir = structured_docs_root / vendor_id
    vendor_dir.mkdir(parents=True, exist_ok=True)

    moc_json = {
        "doc_type": "moc_certificate",
        "page_count": 1,  # Wathq is API data, but we keep the same schema
        "fields": moc_fields,
    }

    output_path = vendor_dir / "moc_certificate.json"
    output_path.write_text(
        json.dumps(moc_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # logger.info("Saved MOC Wathq data for vendor %s to %s", vendor_id, output_path)

# -------------------------
# MOC / Wathq helpers
# -------------------------

def extract_cr_from_portal(portal_json: Dict[str, Any]) -> str | None:
    """
    Try to extract CR number from the portal JSON.

    Adjust keys based on your real portal schema.
    """
    # Likely keys in your portal JSON
    candidate_keys = [
        "CR Number",
        "Cr Number",
        "cr_number",
        "crNumber",
        "commercial_registration_number",
        "commercialRegistrationNumber",
    ]

    # 1) Direct top-level keys
    for key in candidate_keys:
        if key in portal_json and portal_json[key]:
            return str(portal_json[key]).strip()

    # 2) If you have nested 'basic_info' or similar
    for container_key in ("basic_info", "basicInfo", "Basic Information"):
        section = portal_json.get(container_key)
        if isinstance(section, dict):
            for key in candidate_keys:
                if key in section and section[key]:
                    return str(section[key]).strip()

    return None



