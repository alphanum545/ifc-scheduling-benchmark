from __future__ import annotations

from typing import Iterable

from .interface import Scheduler


class AlgorithmRegistry:
    """Small explicit registry for experiment-dispatch algorithm lookup."""

    def __init__(self, schedulers: Iterable[Scheduler] = ()) -> None:
        self._schedulers: dict[str, Scheduler] = {}
        for scheduler in schedulers:
            self.register(scheduler)

    def register(self, scheduler: Scheduler) -> None:
        algorithm_id = scheduler.algorithm_id
        if not isinstance(algorithm_id, str) or not algorithm_id:
            raise ValueError("scheduler algorithm_id must be a non-empty string")
        if algorithm_id in self._schedulers:
            raise ValueError(f"algorithm {algorithm_id!r} is already registered")
        self._schedulers[algorithm_id] = scheduler

    def get(self, algorithm_id: str) -> Scheduler:
        try:
            return self._schedulers[algorithm_id]
        except KeyError as exc:
            raise KeyError(f"unknown algorithm {algorithm_id!r}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._schedulers))
