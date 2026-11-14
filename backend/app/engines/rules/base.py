"""Base class and interfaces for deterministic security indicator rules."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from backend.app.schemas.analysis import (
    IndicatorCategory,
    IndicatorSeverity,
    SecurityIndicator,
)


class BaseSecurityRule(ABC):
    """Abstract base class for all deterministic security rules."""

    def __init__(
        self,
        rule_id: str,
        category: IndicatorCategory,
        severity: IndicatorSeverity,
        explanation: str,
        mitigation: str,
    ):
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.explanation = explanation
        self.mitigation = mitigation

    @abstractmethod
    def evaluate(self, target_data: Any) -> Optional[SecurityIndicator]:
        """Evaluate target data and return SecurityIndicator if triggered."""
        raise NotImplementedError
