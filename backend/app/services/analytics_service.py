import os
import json
import logging
from threading import Lock
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("uvicorn.error")
ANALYTICS_FILE = Path("uploads/analytics.json")
_lock = Lock()

# Global default stats schema
_stats: Dict[str, Any] = {
    "total_analyzed": 0,
    "total_risk_score": 0,
    "average_risk_score": 0.0,
    "contract_types": {}
}

def load_analytics():
    """
    Loads saved analytics data from disk into memory.
    """
    global _stats
    if ANALYTICS_FILE.exists():
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Ensure correct types and default structures are maintained
            _stats = {
                "total_analyzed": int(loaded.get("total_analyzed", 0)),
                "total_risk_score": int(loaded.get("total_risk_score", 0)),
                "average_risk_score": float(loaded.get("average_risk_score", 0.0)),
                "contract_types": dict(loaded.get("contract_types", {}))
            }
            logger.info("Loaded system analytics successfully from disk.")
        except Exception as e:
            logger.error(f"Error loading system analytics from disk: {str(e)}")

def record_analysis(contract_type: str, overall_risk: int):
    """
    Updates global analytics in a thread-safe manner and serializes them.
    Guarantees no raw text or customer details are stored.
    """
    global _stats
    with _lock:
        _stats["total_analyzed"] += 1
        _stats["total_risk_score"] += overall_risk
        _stats["average_risk_score"] = round(_stats["total_risk_score"] / _stats["total_analyzed"], 1)
        
        # Clean type identifier
        c_type = str(contract_type).strip() if contract_type else "Legal Document"
        _stats["contract_types"][c_type] = _stats["contract_types"].get(c_type, 0) + 1
        
        # Serialize to disk
        try:
            os.makedirs(ANALYTICS_FILE.parent, exist_ok=True)
            # Atomic write using rename
            temp_file = ANALYTICS_FILE.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(_stats, f, indent=2)
            os.replace(temp_file, ANALYTICS_FILE)
        except Exception as e:
            logger.error(f"Failed to serialize system analytics: {str(e)}")
            # Cleanup temp if exists
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    os.remove(temp_file)
            except Exception:
                pass

def get_analytics() -> Dict[str, Any]:
    """
    Returns a copy of the current system analytics.
    """
    with _lock:
        return _stats.copy()

# Automatically load existing stats on module import
load_analytics()
