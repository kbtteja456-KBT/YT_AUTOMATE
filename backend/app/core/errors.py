"""Custom exception hierarchy for AI YouTube Shorts Autopilot."""

class AutopilotError(Exception):
    """Base exception for all application errors."""
    pass


class ZeroCostModeViolationError(AutopilotError):
    """Raised when an operation would incur costs while Zero-Cost Mode is enabled."""
    def __init__(self, message: str = "Paid provider blocked by Zero-Cost Mode."):
        super().__init__(message)


class ProviderError(AutopilotError):
    """Base exception for provider-level failures."""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a requested provider is unreachable or offline."""
    pass


class WaitingForFreeProviderError(ProviderError):
    """Raised when no free provider fallback is currently available."""
    pass


class RateLimitExceededError(ProviderError):
    """Raised when an external API rate limit is reached."""
    pass


class QualityControlError(AutopilotError):
    """Base exception for Quality Control failures."""
    pass


class QCScoreThresholdError(QualityControlError):
    """Raised when a rendered video fails to achieve the minimum quality score (90)."""
    def __init__(self, score: float, reasons: list[str]):
        self.score = score
        self.reasons = reasons
        super().__init__(f"QC Gate Failed with score {score:.1f}/100. Reasons: {', '.join(reasons)}")


class YouTubeAPIError(AutopilotError):
    """Base exception for YouTube Data API operations."""
    pass


class DuplicateUploadPreventedError(YouTubeAPIError):
    """Raised when attempting to upload a video that matches a previously published content hash."""
    pass


class JobStateTransitionError(AutopilotError):
    """Raised when an invalid state transition is attempted in the pipeline state machine."""
    pass


class ReconciliationError(AutopilotError):
    """Raised when startup reconciliation encounters an unrecoverable state."""
    pass
