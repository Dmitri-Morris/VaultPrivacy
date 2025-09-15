# vaultprivacy/domain_normalizer.py
import tldextract

def normalize(url: str) -> str:
    if not url:
        return ""
    # tldextract splits host into subdomain, domain, suffix using the Public Suffix List
    ext = tldextract.extract(url)
    if not ext.domain or not ext.suffix:
        # fallback if someone stored a bare word instead of a URL
        return url.lower()
    return f"{ext.domain}.{ext.suffix}".lower()


