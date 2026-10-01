"""Immutable configuration shared by the UI and worker."""
from dataclasses import dataclass

SPEEDS = {"Slow": (0.8, 1.5), "Medium": (0.4, 0.8), "Fast": (0.2, 0.4)}


def normalize_key(key: str) -> str:
    key = str(key).strip()
    if key not in tuple("123456789"):
        raise ValueError("The key must be between 1 and 9.")
    return key


@dataclass(frozen=True)
class RunConfig:
    slots: int = 9
    speed: str = "Fast"
    bias: bool = False
    priority_key: str = "1"
    priority_chance: int = 40
    start_delay: float = 3.0

    def __post_init__(self):
        if not 2 <= self.slots <= 9:
            raise ValueError("The number of slots must be between 2 and 9.")
        if self.speed not in SPEEDS:
            raise ValueError("Choose a speed from the list.")
        if not 0 <= self.priority_chance <= 100:
            raise ValueError("The probability must be between 0 and 100%.")
        if not 0 <= self.start_delay <= 30:
            raise ValueError("The start delay must be between 0 and 30 seconds.")
        object.__setattr__(self, "priority_key", normalize_key(self.priority_key))
        if self.bias and self.priority_key not in self.keys:
            raise ValueError("The priority key must be within the selected slot range.")

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple("123456789"[:self.slots])
