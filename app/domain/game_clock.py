from __future__ import annotations
import time

from app.domain.color import Color


class GameClock:
    white_time: int
    black_time: int
    increment: int
    active_color: Color
    is_running: bool

    def __init__(self, initial_seconds: int, increment_seconds: int = 0):
        self.white_time = initial_seconds
        self.black_time = initial_seconds
        self.increment = increment_seconds
        self.active_color = Color.WHITE
        self.is_running = False
        self._turn_started_at: float | None = None


    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self._turn_started_at = time.monotonic()

    def _elapsed_on_active(self) -> float:
        if not self.is_running or self._turn_started_at is None:
            return 0.0
        return time.monotonic() - self._turn_started_at

    def _apply_elapsed(self) -> None:
        elapsed = self._elapsed_on_active()
        if self.active_color == Color.WHITE:
            self.white_time -= elapsed
        else:
            self.black_time -= elapsed


    def switch_turn(self) -> None:
        if self.is_running:
            self._apply_elapsed()
            if self.active_color == Color.WHITE:
                self.white_time += self.increment
            else:
                self.black_time += self.increment

        self.active_color = self.active_color.get_opposite_color()
        if self.is_running:
            self._turn_started_at = time.monotonic()

    def stop(self) -> None:
        if self.is_running:
            self._apply_elapsed()
            self.is_running = False
            self._turn_started_at = None

    def tick(self) -> None:
        if self.is_running:
            self._apply_elapsed()
            self._turn_started_at = time.monotonic()


    def get_time(self, color: Color) -> float:
        base = self.white_time if color == Color.WHITE else self.black_time
        if self.is_running and color == self.active_color:
            return base - self._elapsed_on_active()
        return base

    def is_time_up(self, color: Color | None = None) -> bool:
        if color is None:
            color = self.active_color
        return self.get_time(color) <= 0