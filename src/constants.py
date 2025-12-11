"""
Constants and configuration values
"""

# Date regex patterns
DATE_PATTERNS = [
    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
    r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',    # YYYY/MM/DD
    r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
    r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
]

# Signature detection keywords
SIGNATURE_KEYWORDS = [
    'signature',
    'signed',
    'sign here',
    'authorized signature',
    'signatory',
    'undersigned'
]

# Stamp detection keywords
STAMP_KEYWORDS = [
    'stamp',
    'seal',
    'official',
    'approved',
    'certified',
    'notarized'
]

# Default OCR configuration
DEFAULT_OCR_CONFIG = {
    'use_angle_cls': True,
    'det_db_thresh': 0.3,
    'rec_batch_num': 6,
    'show_log': False
}

# Signature detection thresholds
SIGNATURE_THRESHOLD = 0.4
SIGNATURE_ASPECT_RATIO_MIN = 2
SIGNATURE_ASPECT_RATIO_MAX = 10
SIGNATURE_AREA_MIN = 1000
SIGNATURE_AREA_MAX = 50000

# Stamp detection thresholds
STAMP_THRESHOLD = 0.5
STAMP_RED_PERCENTAGE_MIN = 0.1

########################################

DEFAULT_DEVICE = None
DEFAULT_USE_TENSORRT = False
DEFAULT_PRECISION = "fp32"
DEFAULT_ENABLE_MKLDNN = True
DEFAULT_MKLDNN_CACHE_CAPACITY = 10
DEFAULT_CPU_THREADS = 10
SUPPORTED_PRECISION_LIST = ["fp32", "fp16"]
DEFAULT_USE_CINN = False
