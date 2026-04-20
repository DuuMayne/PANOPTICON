from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class FailingResource:
    resource_type: str
    resource_identifier: str
    details: dict = field(default_factory=dict)


@dataclass
class EvaluationResult:
    status: Literal["pass", "fail", "error"]
    summary: str
    evidence: dict = field(default_factory=dict)
    failures: list[FailingResource] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class EvaluatorBase(ABC):
    """Base class for all control evaluators.

    Evaluators are pure deterministic functions: they receive data from
    a connector and return a result. No API calls, no side effects.
    """

    @abstractmethod
    def evaluate(self, data: dict, config: dict) -> EvaluationResult:
        """Evaluate control against provided data."""
