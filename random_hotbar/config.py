"""Immutable configuration shared by the UI and worker."""
from dataclasses import dataclass

SPEEDS = {"Медленно": (0.8, 1.5), "Средне": (0.4, 0.8), "Быстро": (0.2, 0.4)}


def normalize_key(key: str) -> str:
    key = str(key).strip()
    if key not in tuple("123456789"):
        raise ValueError("Клавиша должна быть от 1 до 9.")
    return key


@dataclass(frozen=True)
class RunConfig:
    slots: int = 9
    speed: str = "Быстро"
    bias: bool = False
    priority_key: str = "1"
    priority_chance: int = 40
    start_delay: float = 3.0

    def __post_init__(self):
        if not 2 <= self.slots <= 9:
            raise ValueError("Количество клавиш должно быть от 2 до 9.")
        if self.speed not in SPEEDS:
            raise ValueError("Выберите скорость из списка.")
        if not 0 <= self.priority_chance <= 100:
            raise ValueError("Вероятность должна быть от 0 до 100%.")
        if not 0 <= self.start_delay <= 30:
            raise ValueError("Задержка старта должна быть от 0 до 30 секунд.")
        object.__setattr__(self, "priority_key", normalize_key(self.priority_key))
        if self.bias and self.priority_key not in self.keys:
            raise ValueError("Приоритетная клавиша должна входить в выбранный диапазон.")

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple("123456789"[:self.slots])
