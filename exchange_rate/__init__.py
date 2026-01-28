"""
Simple exchange rate client that talks to a public HTTP API.

The module is intentionally independent from the calculator so that
students can evolve each piece separately.

NOTE: Tests mock the network calls so CI never depends on real HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import requests


API_URL = "https://api.frankfurter.app/latest"
DEFAULT_TIMEOUT = 5.0


class ExchangeRateError(Exception):
    """Base error raised by the exchange rate client."""


@dataclass(frozen=True)
class RateQuote:
    """Represents a single FX quote and a derived conversion operation."""

    base: str
    target: str
    rate: float

    def convert(self, amount: float) -> float:
        """Convert ``amount`` from ``base`` currency to ``target`` currency."""
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        return amount * self.rate


def _parse_rate_response(base: str, target: str, payload: Dict[str, Any]) -> RateQuote:
    """Internal helper to validate and parse the API JSON payload."""
    try:
        rates = payload["rates"]
    except KeyError as exc:
        raise ExchangeRateError("Malformed response: missing 'rates' field") from exc

    if not isinstance(rates, dict):
        raise ExchangeRateError("Malformed response: 'rates' must be a mapping")

    try:
        rate = float(rates[target])
    except KeyError as exc:
        raise ExchangeRateError(f"Currency '{target}' not present in response") from exc
    except (TypeError, ValueError) as exc:
        raise ExchangeRateError("Rate must be a numeric value") from exc

    if rate <= 0:
        raise ExchangeRateError("Rate must be positive")

    return RateQuote(base=base.upper(), target=target.upper(), rate=rate)


def fetch_rate(base: str, target: str, timeout: float = DEFAULT_TIMEOUT) -> RateQuote:
    """Fetch a FX rate from the public API.

    Parameters
    ----------
    base:
        Base currency code (e.g. ``'USD'``).
    target:
        Target currency code (e.g. ``'EUR'``).
    timeout:
        Socket timeout passed through to ``requests.get``.

    Returns
    -------
    RateQuote
        A validated quote object that can also convert amounts.

    Raises
    ------
    ExchangeRateError
        For HTTP errors, malformed JSON and other domain-level issues.
    requests.RequestException
        If the underlying HTTP request fails at the transport level.
    """
    params = {"from": base.upper(), "to": target.upper()}

    try:
        response = requests.get(API_URL, params=params, timeout=timeout)
    except requests.RequestException:
        # Bubble up low-level network issues so callers can decide what to do.
        raise

    if response.status_code != 200:
        raise ExchangeRateError(f"HTTP {response.status_code} from exchange API")

    try:
        payload = response.json()
    except ValueError as exc:
        raise ExchangeRateError("Response body was not valid JSON") from exc

    return _parse_rate_response(base.upper(), target.upper(), payload)

