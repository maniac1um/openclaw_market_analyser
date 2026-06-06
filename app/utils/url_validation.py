from urllib.parse import urlparse

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})


def validate_public_http_url(value: str) -> str:
    """Accept only http/https URLs with a host (blocks javascript:, data:, etc.)."""
    cleaned = value.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError("URL must use http or https scheme")
    if not parsed.netloc:
        raise ValueError("URL must include a host")
    return cleaned
