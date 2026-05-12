"""
Tests for custom error classes - ensuring transparent error handling
"""

import pytest

from app.utils.errors import DataValidationError, ExternalAPIError, PaperAnalysisError


def test_paper_analysis_error_basic():
    """Test basic PaperAnalysisError with message only"""
    error = PaperAnalysisError(message="Something went wrong")

    assert str(error) == "Error: Something went wrong"
    assert error.message == "Something went wrong"
    assert error.details == {}
    assert error.suggestion is None


def test_paper_analysis_error_with_details():
    """Test PaperAnalysisError with details"""
    error = PaperAnalysisError(
        message="Failed to process data",
        details={"field": "query", "value": "invalid"},
    )

    error_str = str(error)
    assert "Error: Failed to process data" in error_str
    assert "Details:" in error_str
    assert "field=query" in error_str
    assert "value=invalid" in error_str


def test_paper_analysis_error_with_suggestion():
    """Test PaperAnalysisError with suggestion"""
    error = PaperAnalysisError(
        message="Invalid input",
        suggestion="Please provide a valid search query",
    )

    error_str = str(error)
    assert "Error: Invalid input" in error_str
    assert "Suggestion: Please provide a valid search query" in error_str


def test_paper_analysis_error_full():
    """Test PaperAnalysisError with all parameters"""
    error = PaperAnalysisError(
        message="Operation failed",
        details={"code": 500, "endpoint": "/api/search"},
        suggestion="Try again later",
    )

    error_str = str(error)
    assert "Error: Operation failed" in error_str
    assert "Details:" in error_str
    assert "code=500" in error_str
    assert "endpoint=/api/search" in error_str
    assert "Suggestion: Try again later" in error_str


def test_external_api_error():
    """Test ExternalAPIError formats correctly"""
    error = ExternalAPIError(
        service="OpenAlex",
        status_code=503,
        response_text="Service Unavailable",
        endpoint="/works",
    )

    error_str = str(error)
    assert "Error: Failed to call OpenAlex API" in error_str
    assert "Details:" in error_str
    assert "endpoint=/works" in error_str
    assert "status_code=503" in error_str
    assert "response=Service Unavailable" in error_str
    assert "Suggestion:" in error_str
    assert "Check if OpenAlex API is available" in error_str
    assert "Status code 503" in error_str


def test_external_api_error_truncates_long_response():
    """Test that ExternalAPIError truncates long response texts"""
    long_response = "x" * 300
    error = ExternalAPIError(
        service="TestAPI",
        status_code=500,
        response_text=long_response,
        endpoint="/test",
    )

    error_str = str(error)
    # Response should be truncated to 200 characters
    assert "response=" + "x" * 200 in error_str
    assert len(error.details["response"]) == 200


def test_data_validation_error():
    """Test DataValidationError formats correctly"""
    error = DataValidationError(
        field="query",
        value="",
        reason="Query cannot be empty",
    )

    error_str = str(error)
    assert "Error: Invalid value for field 'query'" in error_str
    assert "Details:" in error_str
    assert "field=query" in error_str
    assert "value=" in error_str
    assert "reason=Query cannot be empty" in error_str
    assert "Suggestion: Please provide a valid query" in error_str
    assert "Query cannot be empty" in error_str


def test_data_validation_error_with_numeric_value():
    """Test DataValidationError with numeric value"""
    error = DataValidationError(
        field="limit",
        value=-1,
        reason="Limit must be positive",
    )

    error_str = str(error)
    assert "field=limit" in error_str
    assert "value=-1" in error_str
    assert "reason=Limit must be positive" in error_str


def test_error_inheritance():
    """Test that custom errors inherit from PaperAnalysisError"""
    api_error = ExternalAPIError("TestAPI", 500, "Error", "/test")
    validation_error = DataValidationError("field", "value", "reason")

    assert isinstance(api_error, PaperAnalysisError)
    assert isinstance(api_error, Exception)
    assert isinstance(validation_error, PaperAnalysisError)
    assert isinstance(validation_error, Exception)


def test_error_can_be_raised_and_caught():
    """Test that errors can be raised and caught properly"""
    with pytest.raises(ExternalAPIError) as exc_info:
        raise ExternalAPIError(
            service="OpenAlex",
            status_code=404,
            response_text="Not Found",
            endpoint="/papers/123",
        )

    assert "Failed to call OpenAlex API" in str(exc_info.value)
    assert exc_info.value.details["status_code"] == 404


def test_error_format_message_called():
    """Test that format_message is called during initialization"""
    error = PaperAnalysisError(
        message="Test",
        details={"key": "value"},
        suggestion="Fix it",
    )

    # format_message should create proper string representation
    formatted = error.format_message()
    assert formatted == str(error.args[0])
    assert "Error: Test" in formatted
    assert "Details: key=value" in formatted
    assert "Suggestion: Fix it" in formatted
