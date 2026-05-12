"""
Custom exceptions with transparent error messages
CRITICAL: No silent failures allowed

Error Philosophy:
- Always surface errors to users
- Include context: what failed, why, how to fix
- Never use generic "something went wrong" messages
"""

from typing import Any, Optional


class PaperAnalysisError(Exception):
    """
    Base exception for all application errors
    Always includes actionable context
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error with full context"""
        parts = [f"Error: {self.message}"]

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")

        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")

        return " | ".join(parts)


class ExternalAPIError(PaperAnalysisError):
    """
    Error calling external API (e.g., OpenAlex)
    Always includes API response details
    """

    def __init__(self, service: str, status_code: int, response_text: str, endpoint: str):
        super().__init__(
            message=f"Failed to call {service} API",
            details={
                "endpoint": endpoint,
                "status_code": status_code,
                "response": response_text[:200],  # Truncate long responses
            },
            suggestion=(
                f"Check if {service} API is available. "
                f"Status code {status_code} may indicate rate limiting or service outage."
            ),
        )


class DataValidationError(PaperAnalysisError):
    """
    Error validating data (e.g., invalid query parameters)
    """

    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"Invalid value for field '{field}'",
            details={"field": field, "value": str(value), "reason": reason},
            suggestion=f"Please provide a valid {field}. {reason}",
        )
