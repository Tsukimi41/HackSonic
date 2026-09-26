from datetime import datetime, timezone

import numpy as np

from extract_planetary_computer import _choose_orbit, _dilate


class Item:
    def __init__(self, date: str, orbit: int, state: str = "descending") -> None:
        self.datetime = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        self.properties = {"sat:relative_orbit": orbit, "sat:orbit_state": state}


def test_choose_orbit_maximizes_weakest_required_window() -> None:
    items = []
    for year in (2024, 2025):
        for month in (3, 4, 5, 6):
            items.append(Item(f"{year}-{month:02d}-01", 46))
    # 軌道99は合計数が多くても2025年の湛水期が0件なので選ばない。
    items.extend(Item(f"2024-{month:02d}-{day:02d}", 99)
                 for month in (3, 4, 5, 6) for day in (1, 10, 20))
    items.extend(Item(f"2025-{month:02d}-{day:02d}", 99)
                 for month in (3, 4) for day in (1, 10, 20))
    assert _choose_orbit(items) == 46


def test_cloud_buffer_expands_two_pixels() -> None:
    mask = np.zeros((7, 7), dtype=bool)
    mask[3, 3] = True
    dilated = _dilate(mask, radius=2)
    assert dilated.sum() == 25
    assert dilated[1:6, 1:6].all()

