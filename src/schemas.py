# ============================================
"""
Data schemas and models for OCR results
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import json


@dataclass
class OCRResult:
    """Data class for OCR results"""
    file_path: str
    page_count: int
    text_content: str
    extracted_fields: Dict[str, Any]
    dates_found: List[str]
    has_signature: bool
    has_stamp: bool
    signature_confidence: float
    stamp_confidence: float
    processing_time: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
