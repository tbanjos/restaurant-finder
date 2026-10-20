"""Immutable pipeline of application steps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from .pipeline_step import ContextT, PipelineStep


@dataclass(frozen=True)
class Pipeline(Generic[ContextT]):
    """An ordered, immutable collection of :class:`PipelineStep` objects."""

    steps: tuple[PipelineStep[ContextT], ...]

    def run(self, context: ContextT) -> ContextT:
        """Run every step in order and return the mutated context."""
        for step in self.steps:
            step.run(context)
        return context

    def __iter__(self):
        return iter(self.steps)

    def __len__(self) -> int:
        return len(self.steps)
