import http.client
import ipaddress
import socket
import ssl
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
            return True
        if not infos:
            return True
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


def _resolve_allowed_ips(hostname: str) -> list[str]:
    host = (hostname or "").strip().lower().rstrip(".")
    if is_blocked_host(host):
        raise ValueError("URL host is not allowed for server-side fetch")
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("URL host is not allowed for server-side fetch") from exc
        if not infos:
            raise ValueError("URL host is not allowed for server-side fetch")
        ips: list[str] = []
        for info in infos:
            ip = info[4][0]
            addr = ipaddress.ip_address(ip)
            if _is_private_or_reserved(addr):
                raise ValueError("URL host resolves to a private address")
            if ip not in ips:
                ips.append(ip)
        return ips
    if _is_private_or_reserved(addr):
        raise ValueError("URL host is not allowed for server-side fetch")
    return [str(addr)]


def validate_outbound_http_url(url: str) -> str:
    """Reject URLs that resolve to private/link-local/metadata targets (SSRF guard)."""
    from app.utils.url_validation import validate_public_http_url

    cleaned = validate_public_http_url(url)
    parsed = urlparse(cleaned)
    if is_blocked_host(parsed.hostname or ""):
        raise ValueError("URL host is not allowed for server-side fetch")
    return cleaned


def fetch_public_http_url(
    url: str,
    *,
    timeout: float = 12.0,
    max_bytes: int = 400_000,
) -> tuple[bytes, int | None]:
    """Fetch a public HTTP(S) URL with SSRF checks, IP-bound connect, and no redirects."""
    cleaned = validate_outbound_http_url(url)
    parsed = urlparse(cleaned)
    scheme = parsed.scheme
    host = parsed.hostname or ""
    port = parsed.port or (443 if scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    target_ip = _resolve_allowed_ips(host)[0]
    sock = socket.create_connection((target_ip, port), timeout=timeout)
    sock.settimeout(timeout)
    stream: socket.socket | ssl.SSLSocket = sock
    try:
        if scheme == "https":
            ctx = ssl.create_default_context()
            stream = ctx.wrap_socket(sock, server_hostname=host)

        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "User-Agent: Mozilla/5.0 OpenClaw-Monitor/1.0\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        stream.sendall(request.encode("latin-1"))

        response = http.client.HTTPResponse(stream)
        response.begin()
        if response.status in {301, 302, 303, 307, 308}:
            raise ValueError("HTTP redirects are not allowed for server-side fetch")
        if response.status is not None and response.status >= 400:
            raise ValueError(f"HTTP {response.status}")
        body = response.read(max_bytes + 1)
        return body[:max_bytes], response.status
    finally:
        try:
            stream.close()
        except OSError:
            pass
