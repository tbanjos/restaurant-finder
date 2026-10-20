"""Small, typed pipeline primitives.

The pipeline pattern is used to keep the application's data flow explicit:
each stage receives the same context object, mutates the fields it owns, and
returns control to the pipeline. Stages are deliberately independent so they
can be reordered, replaced, or tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

ContextT = TypeVar("ContextT")


@runtime_checkable
class PipelineStep(Protocol[ContextT]):
    """A single, named unit of work in a pipeline."""

    name: str

    def run(self, context: ContextT) -> None:
        """Apply this step to ``context``."""
        ...


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
