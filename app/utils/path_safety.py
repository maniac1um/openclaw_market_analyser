import uuid
from pathlib import Path


def parse_uuid(value: str) -> str | None:
    """Return canonical UUID string or None if invalid."""
    try:
        return str(uuid.UUID(str(value).strip()))
    except (ValueError, AttributeError):
        return None


def safe_child_path(root: Path, name: str, *, suffix: str = "") -> Path | None:
    """
    Resolve root / (name + suffix) and ensure the result stays under root.
    Returns None when name is unsafe (traversal) or empty.
    """
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        return None
    base = root.resolve()
    candidate = (base / f"{name}{suffix}").resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate
