"""
Tests for the exchange_rate module.

These are intentionally a bit more "real-world":
- They exercise HTTP integration via a public API shape (but mocked).
- They validate error handling and edge cases.
"""

from __future__ import annotations

import json

import pytest
import requests
import responses

from exchange_rate import ExchangeRateError, RateQuote, fetch_rate


@pytest.fixture
def api_url():
    from exchange_rate import API_URL

    return API_URL


@responses.activate
def test_fetch_rate_success(api_url):
    """Happy-path: we get a valid rate back and can convert amounts."""
    payload = {"base": "USD", "rates": {"EUR": 0.9}}
    responses.add(
        responses.GET,
        api_url,
        match=[responses.matchers.query_param_matcher({"from": "USD", "to": "EUR"})],
        json=payload,
        status=200,
    )

    quote = fetch_rate("usd", "eur")  # case-insensitivity

    assert isinstance(quote, RateQuote)
    assert quote.base == "USD"
    assert quote.target == "EUR"
    assert quote.rate == pytest.approx(0.9)
    assert quote.convert(100) == pytest.approx(90.0)


@responses.activate
def test_fetch_rate_handles_http_error(api_url):
    """Non-200 responses should surface as domain errors."""
    responses.add(
        responses.GET,
        api_url,
        status=503,
    )

    with pytest.raises(ExchangeRateError) as excinfo:
        fetch_rate("USD", "EUR")

    assert "HTTP 503" in str(excinfo.value)


@responses.activate
def test_fetch_rate_handles_malformed_json(api_url):
    """If the API returns invalid JSON, we raise a clear error."""
    responses.add(
        responses.GET,
        api_url,
        body="not-json",
        status=200,
        content_type="text/plain",
    )

    with pytest.raises(ExchangeRateError) as excinfo:
        fetch_rate("USD", "EUR")

    assert "valid JSON" in str(excinfo.value)


@responses.activate
def test_fetch_rate_handles_missing_rates_field(api_url):
    """Defensive checks for unexpected API shapes."""
    payload = {"base": "USD"}  # missing "rates"
    responses.add(
        responses.GET,
        api_url,
        json=payload,
        status=200,
    )

    with pytest.raises(ExchangeRateError) as excinfo:
        fetch_rate("USD", "EUR")

    assert "missing 'rates'" in str(excinfo.value)


@responses.activate
def test_fetch_rate_handles_unknown_currency(api_url):
    """Asking for a symbol that is not present should fail loudly."""
    payload = {"base": "USD", "rates": {"GBP": 0.8}}
    responses.add(
        responses.GET,
        api_url,
        json=payload,
        status=200,
    )

    with pytest.raises(ExchangeRateError) as excinfo:
        fetch_rate("USD", "EUR")

    assert "Currency 'EUR' not present" in str(excinfo.value)


@responses.activate
def test_fetch_rate_propagates_network_errors(api_url):
    """Low-level transport errors are bubbled up as RequestException."""

    def _raise_timeout(_request):
        raise requests.Timeout("connection timed out")

    responses.add_callback(
        responses.GET,
        api_url,
        callback=_raise_timeout,
    )

    with pytest.raises(requests.Timeout):
        fetch_rate("USD", "EUR", timeout=0.001)


def test_rate_quote_convert_negative_amount():
    """The conversion helper should guard against obviously bad input."""
    quote = RateQuote(base="USD", target="EUR", rate=0.9)

    with pytest.raises(ValueError):
        quote.convert(-1)


@pytest.mark.parametrize(
    "amount,rate,expected",
    [
        (0, 1.0, 0.0),
        (100, 1.0, 100.0),
        (50, 0.5, 25.0),
        (123.45, 1.2345, pytest.approx(152.39, rel=1e-4)),
    ],
)
def test_rate_quote_convert_parametrized(amount, rate, expected):
    """Parametrized test for conversion math."""
    quote = RateQuote(base="AAA", target="BBB", rate=rate)
    assert quote.convert(amount) == expected

