"""Key selection, independent of the UI and operating system."""
import random
from .config import RunConfig


def choose_key(config: RunConfig, rng=random) -> str:
    if not config.bias:
        return rng.choice(config.keys)
    if rng.random() < config.priority_chance / 100:
        return config.priority_key
    remaining = tuple(key for key in config.keys if key != config.priority_key)
    return rng.choice(remaining)
