import ipaddress
import socket
from urllib.parse import urlparse


def is_blocked_host(hostname: str) -> bool:
    host = (hostname or "").strip().lower().rstrip(".")
    if not host:
        return True
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return True
    if host.endswith(".local") or host.endswith(".internal"):
        return True
    if host in {"metadata.google.internal", "169.254.169.254"}:
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        for info in infos:
            ip = info[4][0]
            try:
                addr = ipaddress.ip_address(ip)
            except ValueError:
                continue
            if _is_private_or_reserved(addr):
                return True
        return False
    return _is_private_or_reserved(addr)


def _is_private_or_reserved(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
    )


def validate_outbound_http_url(url: str) -> str:
    """Reject URLs that resolve to private/link-local/metadata targets (SSRF guard)."""
    from app.utils.url_validation import validate_public_http_url

    cleaned = validate_public_http_url(url)
    parsed = urlparse(cleaned)
    if is_blocked_host(parsed.hostname or ""):
        raise ValueError("URL host is not allowed for server-side fetch")
    return cleaned
