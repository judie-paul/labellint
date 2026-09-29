"""Deterministic largest-remainder allocation of annotator profiles."""

import numpy as np

from labellint.schema import Profile

PROFILES: tuple[Profile, ...] = ("diligent", "rusher", "copy_paster", "random_clicker", "biased")
SHARES = np.array([0.70, 0.08, 0.08, 0.07, 0.07])


def profile_pool(count: int, rng: np.random.Generator) -> list[Profile]:
    """Allocate exact pool size with deterministic tie-breaking, then shuffle."""
    if count < 1:
        raise ValueError("annotator count must be positive")
    expected = SHARES * count
    allocated = np.floor(expected).astype(int)
    order = np.argsort(-(expected - allocated), kind="stable")
    for index in order[: count - int(allocated.sum())]:
        allocated[index] += 1
    pool = [profile for profile, size in zip(PROFILES, allocated, strict=True) for _ in range(size)]
    rng.shuffle(pool)
    return pool
