# src/schemas/constants.py

DOC_TYPE_MAPPING = {
    # filename stem      -> logical doc_type used in validation_config
    "VAT": "vat_certificate",
    "IBAN": "iban_letter",
    "chamber_of_commerce": "chamber_certificate",
    "code_of_conduct": "code_of_conduct",
    "nda": "nda",
    "zatca": "zatca_certificate",
    "GOSI": "gosi_certificate",
    "nationalization": "nationalization_certificate",
    "portal_excel_quality": "portal_excel_quality",
}

# optional: default when nothing matches and no CLI override is given
DEFAULT_DOC_TYPE = "generic_document"
