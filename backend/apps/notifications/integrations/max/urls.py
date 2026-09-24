import ipaddress
from urllib.parse import urlsplit


def is_public_https_url(value: str) -> bool:
    try:
        parsed = urlsplit((value or '').strip())
        hostname = parsed.hostname
    except (TypeError, ValueError):
        return False
    if parsed.scheme.lower() != 'https' or not hostname:
        return False
    normalized_host = hostname.rstrip('.').lower()
    if normalized_host == 'localhost' or normalized_host.endswith((
        '.localhost', '.local', '.test', '.invalid',
    )):
        return False
    try:
        return ipaddress.ip_address(normalized_host).is_global
    except ValueError:
        return '.' in normalized_host
