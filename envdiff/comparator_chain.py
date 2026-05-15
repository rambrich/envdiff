"""Chain multiple diff results through a pipeline of checks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from envdiff.differ import DiffResult


# A step is a callable that receives a DiffResult and returns a DiffResult
# (possibly filtered, sorted, or annotated).
ChainStep = Callable[[DiffResult], DiffResult]


@dataclass
class ChainResult:
    """Outcome of running a DiffResult through a comparator chain."""

    source: str
    target: str
    steps_applied: int
    result: DiffResult
    step_names: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ChainResult(source={self.source!r}, target={self.target!r}, "
            f"steps={self.steps_applied}, issues={self.result.has_issues})"
        )

    @property
    def has_issues(self) -> bool:
        return self.result.has_issues


@dataclass
class ComparatorChain:
    """Ordered collection of transformation steps applied to a DiffResult."""

    steps: List[tuple[str, ChainStep]] = field(default_factory=list)

    def add_step(self, name: str, fn: ChainStep) -> "ComparatorChain":
        """Append a named step and return self for chaining."""
        self.steps.append((name, fn))
        return self

    def run(self, diff: DiffResult) -> ChainResult:
        """Execute all steps in order and return a ChainResult."""
        current = diff
        names: List[str] = []
        for name, fn in self.steps:
            current = fn(current)
            names.append(name)
        return ChainResult(
            source=diff.source,
            target=diff.target,
            steps_applied=len(self.steps),
            result=current,
            step_names=names,
        )


def build_chain(*steps: tuple[str, ChainStep]) -> ComparatorChain:
    """Convenience constructor: build a ComparatorChain from (name, fn) pairs."""
    chain = ComparatorChain()
    for name, fn in steps:
        chain.add_step(name, fn)
    return chain
