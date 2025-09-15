# vaultprivacy/api_client.py
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Dict, Optional
import requests

CACHE_FILE = Path(".cache_tosdr.json")
BASE_SEARCH = "https://api.tosdr.org/search/v4/"
BASE_SERVICE_V2 = "https://api.tosdr.org/service/v2/"
TIMEOUT = 10
SLEEP_BETWEEN = 0.3

def _load_cache() -> Dict[str, Dict]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_cache(cache: Dict[str, Dict]) -> None:
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def _best_match(search_json: Dict, domain: str) -> Optional[Dict]:
    """
    Pick a service from a search response. Very simple heuristic.
    """
    if not search_json or "parameters" not in search_json:
        return None
    
    services = search_json["parameters"].get("services", [])
    if not services:
        return None
    
    # exact domain match first
    for service in services:
        if isinstance(service, dict):
            urls = service.get("urls", [])
            if any(domain in url for url in urls):
                return service
    
    # otherwise take the first service if present
    if services:
        return services[0]
    
    return None

def lookup_tosdr(domain: str) -> Dict:
    """
    Returns a dict with keys: grade, service_id, name.
    grade can be A B C D E or Unknown.
    """
    cache = _load_cache()
    if domain in cache:
        return cache[domain]

    out = {"grade": "Unknown", "service_id": None, "name": domain}

    try:
        # 1) search by domain
        resp = requests.get(BASE_SEARCH, params={"query": domain}, timeout=TIMEOUT)
        if resp.ok:
            service = _best_match(resp.json(), domain)
            if service:
                # Extract data directly from search response
                name = service.get("name", domain)
                rating = service.get("rating", {})
                if isinstance(rating, dict) and "letter" in rating:
                    grade = rating["letter"]
                else:
                    grade = "Unknown"
                
                service_id = service.get("id")
                if service_id:
                    service_id = int(service_id)

                out = {"grade": grade if grade in list("ABCDE") else "Unknown",
                       "service_id": service_id,
                       "name": name}
    except requests.RequestException:
        pass  # keep Unknown on errors

    # cache and pause to be polite
    cache[domain] = out
    _save_cache(cache)
    time.sleep(SLEEP_BETWEEN)
    return out
