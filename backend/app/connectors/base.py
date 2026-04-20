from __future__ import annotations

from abc import ABC, abstractmethod


class ConnectorBase(ABC):
    """Base class for all external system connectors."""

    @abstractmethod
    def fetch(self, config: dict) -> dict:
        """Fetch data needed by evaluators. Returns normalized data."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify credentials and connectivity."""


class MockConnector(ConnectorBase):
    """Returns static mock data for development and testing."""

    def __init__(self, mock_data: dict | None = None):
        self._mock_data = mock_data or {}

    def fetch(self, config: dict) -> dict:
        return self._mock_data

    def test_connection(self) -> bool:
        return True
