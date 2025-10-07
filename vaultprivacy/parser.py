#!/usr/bin/env python3
import json, re, sys
from urllib.parse import urlparse

# Common multi-part TLDs to catch simple cases without extra deps
MULTIPART_TLDS = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "co.jp", "com.br"}

def normalize_domain(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip().lower()

    # If it looks like an email, bail
    if "@" in s and "://" not in s:
        return ""

    # Ensure we can parse with urlparse
    if "://" not in s:
        s = "https://" + s
    parsed = urlparse(s)

    host = parsed.hostname or ""
    if not host:
        return ""

    # Strip obvious prefixes
    host = re.sub(r"^(www\.|m\.)", "", host)

    parts = host.split(".")
    if len(parts) < 2:
        return host

    last_two = ".".join(parts[-2:])
    last_three = ".".join(parts[-3:]) if len(parts) >= 3 else ""

    # Handle common multi-part TLDs like co.uk, com.au, etc
    if last_two in MULTIPART_TLDS and len(parts) >= 3:
        return ".".join(parts[-3:])
    if last_three in MULTIPART_TLDS and len(parts) >= 4:
        return ".".join(parts[-4:])

    return last_two

def extract_domains(bitwarden_json_path: str) -> list[str]:
    data = json.loads(open(bitwarden_json_path, "r", encoding="utf-8").read())
    items = data.get("items", [])
    seen = set()
    ordered = []
    for it in items:
        login = it.get("login", {}) or {}
        uris = login.get("uris") or []
        # Bitwarden exports place the URL in login.uris[].uri
        # We only need one domain per item
        for u in uris:
            raw = (u or {}).get("uri", "")
            dom = normalize_domain(raw)
            if dom and dom not in seen:
                seen.add(dom)
                ordered.append(dom)
    return ordered

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_domains.py path/to/bitwarden_export.json")
        sys.exit(1)
    print(f"Processing file: {sys.argv[1]}")
    domains = extract_domains(sys.argv[1])
    print(f"Found {len(domains)} domains:")
    for d in domains:
        print(f"  {d}")
