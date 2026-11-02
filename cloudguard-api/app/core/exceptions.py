"""
CloudGuard Core Disaster Recovery Exceptions.
"""

class CloudGuardException(Exception):
    """Base exception for all CloudGuard DR operations."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UnsafeRestoreTargetError(CloudGuardException):
    """Raised when a restore operation targets the production/primary database or unsafe destination."""
    pass

SafetyInterlockError = UnsafeRestoreTargetError


class BackupCreationError(CloudGuardException):
    """Raised when snapshot or dump creation fails."""
    pass


class CorruptedBackupError(CloudGuardException):
    """Raised when a backup archive fails checksum or payload integrity checks."""
    pass


class IsolatedRestoreError(CloudGuardException):
    """Raised when restoring into the isolated target database fails."""
    pass

RestoreFailureError = IsolatedRestoreError


class IntegrityValidationError(CloudGuardException):
    """Raised when restored data differs from primary source data or violates constraints."""
    pass


class SchemaDriftError(CloudGuardException):
    """Raised when restored schema does not match the expected application schema."""
    pass


class ProviderConfigurationError(CloudGuardException):
    """Raised when AWS or Local configuration is invalid or missing required credentials."""
    pass
