"""verify_agent URL 抓取测试（mock httpx）"""
from unittest.mock import MagicMock, patch

from hh_research.extract.researcher_mapping.verify_agent import (
    fetch_url_text,
    fetch_all_urls,
)


def _mock_response(text: str, status: int = 200):
    r = MagicMock()
    r.status_code = status
    r.text = text
    return r


def test_fetch_url_text_success():
    with patch("httpx.Client") as Client:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _mock_response("<title>Tri Dao</title>" * 100)
        Client.return_value = client
        result = fetch_url_text("https://github.com/tridao")
    assert result is not None
    assert "Tri Dao" in result


def test_fetch_url_text_timeout_returns_none():
    import httpx

    with patch("httpx.Client") as Client:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.side_effect = httpx.TimeoutException("timeout")
        Client.return_value = client
        result = fetch_url_text("https://slow.example.com")
    assert result is None


def test_fetch_url_text_http_error_returns_none():
    with patch("httpx.Client") as Client:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _mock_response("", status=404)
        Client.return_value = client
        result = fetch_url_text("https://example.com/missing")
    assert result is None


def test_fetch_url_text_cap_200kb():
    huge = "x" * (300_000)
    with patch("httpx.Client") as Client:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _mock_response(huge)
        Client.return_value = client
        result = fetch_url_text("https://example.com/huge")
    assert result is not None
    assert len(result) <= 200_000


def test_fetch_all_urls_concurrent():
    def _get(url, **kw):
        return _mock_response(f"page-{url}")

    with patch("httpx.Client") as Client:
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.side_effect = _get
        Client.return_value = client
        urls = {"github": "https://github.com/x", "homepage": "https://x.me"}
        result = fetch_all_urls(urls)
    assert "github" in result and "page-https://github.com/x" in result["github"]
    assert "homepage" in result and "page-https://x.me" in result["homepage"]
