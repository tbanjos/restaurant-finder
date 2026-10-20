"""Protocol shared by pipeline stages."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

ContextT = TypeVar("ContextT")


@runtime_checkable
class PipelineStep(Protocol[ContextT]):
    """A single, named unit of work in a pipeline."""

    name: str

    def run(self, context: ContextT) -> None:
        """Apply this step to ``context``."""
        ...
