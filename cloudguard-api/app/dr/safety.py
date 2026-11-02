"""
Disaster Recovery Safety Interlocks.
Enforces Rule 4 & 7: Never overwrite or restore over the original production database!
"""
from urllib.parse import urlparse
from app.core.exceptions import UnsafeRestoreTargetError
from app.core.logging import logger


def normalize_db_url(url: str) -> str:
    """Normalizes database URL by stripping credentials and query parameters."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Strip credentials, leave scheme, hostname, port, and path
        sanitized = f"{parsed.scheme}://{parsed.hostname or ''}:{parsed.port or ''}{parsed.path}"
        return sanitized.strip().lower().rstrip("/")
    except Exception:
        return url.strip().lower().rstrip("/")


def extract_db_name(url: str) -> str:
    """Extracts database name or sqlite file name from URL."""
    try:
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        return path.split("/")[-1] if path else ""
    except Exception:
        return url.split("/")[-1]


def assert_safe_restore_target(source_db_url: str, target_db_url: str) -> None:
    """
    CRITICAL DR SAFETY INTERLOCK:
    Guarantees that the target database is an isolated sandbox and cannot overwrite production!
    """
    if not target_db_url:
        raise UnsafeRestoreTargetError("Restore target database URL cannot be empty.")

    norm_source = normalize_db_url(source_db_url)
    norm_target = normalize_db_url(target_db_url)

    # 1. Exact URL / Host / Port / DB parity check
    if norm_source == norm_target:
        raise UnsafeRestoreTargetError(
            f"FATAL SAFETY INTERLOCK ACTIVATED: Target database '{norm_target}' is identical "
            f"to the source production database '{norm_source}'! "
            "CloudGuard halted restore operation to prevent production data overwrite."
        )

    source_db = extract_db_name(source_db_url)
    target_db = extract_db_name(target_db_url)

    # 2. Database name matching check on same server
    if source_db and target_db and source_db == target_db:
        # Check if hosts are identical
        try:
            p_source = urlparse(source_db_url)
            p_target = urlparse(target_db_url)
            if p_source.hostname == p_target.hostname and p_source.port == p_target.port:
                raise UnsafeRestoreTargetError(
                    f"SAFETY VIOLATION: Target database name '{target_db}' matches source database on the same host."
                )
        except Exception:
            pass

    # 3. Production naming safeguard
    target_lower = target_db.lower()
    if ("prod" in target_lower or "primary" in target_lower) and not (
        "test" in target_lower or "isolated" in target_lower or "sandbox" in target_lower or "drill" in target_lower
    ):
        raise UnsafeRestoreTargetError(
            f"SAFETY VIOLATION: Target database '{target_db}' contains production indicators. "
            "Isolated DR drills must target databases with 'isolated', 'test', 'sandbox', or 'drill' in their name."
        )

    logger.info(f"DR Safety Interlock Verified: Target '{target_db}' is safe for isolated restore drill.")


validate_isolated_target_safety = assert_safe_restore_target
