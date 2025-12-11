import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Logger setup
# -------------------------
logger = logging.getLogger(__name__)


# -------------------------
# Wathq client
# -------------------------
def get_moc_basic_info(cr_number: str) -> Optional[Dict[str, str]]:
    """
    Fetch ONLY from Wathq:
    - CR National Number
    - Company Name
    - Issue Date (Gregorian)
    """

    api_key = os.getenv("WATHQ_API_KEY")  # ✅ STRICT ENV VARIABLE
    if not api_key:
        logger.error("WATHQ_API_KEY is not set in environment variables.")
        raise ValueError("WATHQ_API_KEY is not set in environment variables.")

    url = f"https://api.wathq.sa/commercial-registration/fullinfo/{cr_number}"

    headers = {
        "accept": "application/json",
        "apikey": api_key,
    }

    logger.info(f"Fetching Wathq data for CR number: {cr_number}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for CR {cr_number}: {str(e)}")
        return None

    if response.status_code != 200:
        logger.error(f"Wathq API error for CR {cr_number} - Status {response.status_code}: {response.text}")
        return None

    raw = response.json()

    cr_national_number = (
        raw.get("commercialRegistrationNumber")
        or raw.get("crNumber")
        or raw.get("id")
    )

    company_name = (
        raw.get("commercialName")
        or raw.get("tradeName")
        or raw.get("entityName")
        or raw.get("name")
    )

    issue_date_gregorian = (
        raw.get("issueDateGregorian")
        or raw.get("issueDate")
        or raw.get("registrationDate")
    )

    result = {
        "cr_number": str(cr_national_number) if cr_national_number else None,
        "company_name": company_name,
        "issue_date_gregorian": issue_date_gregorian,
    }

    logger.info(f"Successfully extracted Wathq data for CR {cr_number}: {company_name}")
    logger.debug(f"Extracted data: {result}")

    return result


# -------------------------
# Save as structured doc
# -------------------------
def save_moc_structured_json(
    vendor_id: str,
    output_root: Path,
    moc_fields: Dict[str, str],
) -> Path:
    """
    Save Wathq result as:
    <output_root>/<vendor_id>/moc_certificate.json
    """

    vendor_dir = output_root / vendor_id
    vendor_dir.mkdir(parents=True, exist_ok=True)

    moc_json = {
        "doc_type": "moc_certificate",
        "page_count": 1,
        "fields": moc_fields,
    }

    output_path = vendor_dir / "moc_certificate.json"
    output_path.write_text(
        json.dumps(moc_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(f"Saved MOC certificate to: {output_path}")
    return output_path


# -------------------------
# CLI entry point
# -------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    parser = argparse.ArgumentParser(description="Fetch Wathq MOC data and save as structured JSON.")
    parser.add_argument(
        "--vendor-id",
        required=True,
        help="Vendor ID (used as output folder name)."
    )
    parser.add_argument(
        "--cr-number",
        required=True,
        help="Commercial Registration (CR) number to query Wathq."
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Root output folder (e.g. extracted_results_structured)."
    )

    args = parser.parse_args()

    vendor_id = args.vendor_id
    cr_number = args.cr_number
    output_root = args.output_root

    logger.info(f"Running Wathq MOC extraction for vendor={vendor_id}, CR={cr_number}")

    moc_data = get_moc_basic_info(cr_number)

    if not moc_data:
        logger.error("No data returned from Wathq. Nothing was saved.")
        raise SystemExit(1)

    save_moc_structured_json(
        vendor_id=vendor_id,
        output_root=output_root,
        moc_fields=moc_data,
    )

    logger.info("✅ MOC extraction + save completed successfully.")
