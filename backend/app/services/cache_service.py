import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

# Setup cache path relative to application root
CACHE_DIR = Path("uploads/cache")
_memory_cache: Dict[str, Dict[str, Any]] = {}

def get_contract_hash(text: str) -> str:
    """
    Computes SHA-256 hash of the normalized contract text.
    """
    # Normalize whitespace to ensure consistent hashes for identical content
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def get_cached_analysis(text: str) -> Optional[Dict[str, Any]]:
    """
    Checks the in-memory cache and local file system cache for an existing analysis.
    Returns the cached analysis dictionary if found, otherwise None.
    """
    cache_key = get_contract_hash(text)
    
    # 1. Check in-memory cache
    if cache_key in _memory_cache:
        logger.info(f"Cache hit (in-memory) for key: {cache_key[:8]}")
        return _memory_cache[cache_key]
        
    # 2. Check persistent filesystem cache
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Store back in memory for faster subsequent lookups
            _memory_cache[cache_key] = data
            logger.info(f"Cache hit (disk) for key: {cache_key[:8]}")
            return data
        except Exception as e:
            logger.error(f"Failed to read cached analysis from disk: {str(e)}")
            
    return None

def cache_analysis(text: str, result: Dict[str, Any]):
    """
    Saves an analysis result to both in-memory and persistent filesystem cache.
    """
    cache_key = get_contract_hash(text)
    
    # 1. Save in-memory
    _memory_cache[cache_key] = result
    
    # 2. Save on disk
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_file = CACHE_DIR / f"{cache_key}.json"
        
        # Write to a temp file and rename (atomic write to prevent corruption)
        temp_file = cache_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        os.replace(temp_file, cache_file)
        logger.info(f"Successfully cached analysis result to disk: {cache_key[:8]}")
    except Exception as e:
        logger.error(f"Failed to write analysis result to cache file: {str(e)}")
        # Cleanup temp file if exists
        try:
            if 'temp_file' in locals() and temp_file.exists():
                os.remove(temp_file)
        except Exception:
            pass
