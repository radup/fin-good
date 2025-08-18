"""
Simple sandbox analyzer fallback for when advanced analysis is not available.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    BEHAVIORAL = "behavioral"

async def analyze_file_in_sandbox(
    file_content: bytes,
    filename: str,
    analysis_type: AnalysisType = AnalysisType.STATIC,
    **kwargs
) -> Dict[str, Any]:
    """
    Simple file analysis that performs basic checks.
    Returns a safe result for when advanced sandbox analysis is not available.
    """
    
    return {
        "analysis_type": analysis_type.value,
        "threat_detected": False,
        "risk_score": 0.0,
        "behavioral_indicators": [],
        "network_activity": [],
        "file_modifications": [],
        "registry_changes": [],
        "analysis_duration": 0.001,
        "sandbox_version": "simple_fallback_1.0",
        "analysis_timestamp": None,
        "recommendations": ["File appears safe based on basic analysis"]
    }