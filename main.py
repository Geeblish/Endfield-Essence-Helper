from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
import sys
from typing import Iterable, List, Tuple, Union

from Essence_Helper import Stat, WeaponIndex
from audio_helper import chime
from lookup_driver import LookupDriver, GuardMode

def resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel


def data_path(rel: str) -> Path:
    """Prefer external data next to the exe; fallback to bundled resource."""
    external = Path.cwd() / rel
    if external.exists():
        return external
    return resource_path(rel)


WEAPON_JSON = data_path("data/weapons.json")
HOTKEY = "f10"  # user-changeable toggle
LOG_DEBUG = False  # verbose logging toggle
SAVE_IMAGES = False  # set True when you need dumps in data/tmp/ocr_debug
GUARD_MODE = GuardMode.IMAGE  # IMAGE | OCR | NONE
USE_STAT_CACHE = True        # use cache lookups
CREATE_STAT_CACHE = False     # if True, save matched stat images to data/matched
USE_QUALITY_GUARD = False     # set False to skip gold pixel check (e.g., to see lower rarity)
REQUIRE_THREE_STATS = True    # require all 3 stats before lookup


# ---------- Persistence helpers ----------

def _stat_list_from_json(items: Iterable[str]) -> List[Stat]:
    stats: List[Stat] = []
    for name in items:
        try:
            stats.append(Stat[name])
        except KeyError:
            print(f"[WARN] Unknown stat in JSON: {name}", file=sys.stderr)
    return stats


def load_index_from_json(path: Path) -> WeaponIndex:
    data = json.loads(path.read_text(encoding="utf-8"))
    index = WeaponIndex()
    for weapon in data.get("weapons", []):
        name = weapon.get("name")
        stats = _stat_list_from_json(weapon.get("stats", []))
        if not name or len(stats) < 2:
            continue
        index.add_weapon(name, *stats)
    return index


def export_index_to_json(index: WeaponIndex, path: Path) -> None:
    payload = {
        "weapons": [
            {"name": name, "stats": [s.name for s in stats]}
            for name, stats in index.weapons.items()
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[INFO] Exported {len(index.weapons)} weapons -> {path}")


def bootstrap_index(path: Path) -> WeaponIndex:
    if path.exists():
        print(f"[INFO] Loading weapons from {path}")
        return load_index_from_json(path)

    print("[INFO] weapons.json not found, importing from setup.py")
    setup = importlib.import_module("setup")
    index: WeaponIndex = setup.index  # uses the populated index from setup.py
    export_index_to_json(index, path)
    return index


# ---------- Lookup flow ----------

def run_lookup_loop(index: WeaponIndex, hotkey: str = HOTKEY) -> None:
    try:
        import keyboard  # type: ignore
    except ImportError:
        print("Please install `keyboard` for hotkey support: pip install keyboard")
        sys.exit(1)

    driver = LookupDriver(
        save_images=SAVE_IMAGES,
        log_debug=LOG_DEBUG,
        guard_mode=GUARD_MODE,
        use_stat_cache=USE_STAT_CACHE,
        create_stat_cache=CREATE_STAT_CACHE,
        require_three_stats=REQUIRE_THREE_STATS,
    )
    driver.use_quality_guard = USE_QUALITY_GUARD
    active = False

    def toggle():
        nonlocal active
        active = not active
        state = "ON" if active else "OFF"
        print(f"[INFO] Toggled capture {state}")

    keyboard.add_hotkey(hotkey, toggle)
    print(f"[INFO] Press {hotkey.upper()} to toggle continuous capture. Ctrl+C to exit.")

    try:
        while True:
            if not active:
                time.sleep(0.1)
                continue

            stats_tuple = driver.stat_tuple()
            if not stats_tuple:
                if LOG_DEBUG and getattr(driver, "_last_logs", None):
                    for line in driver._last_logs:
                        print(line)
                    driver._last_logs = []
                time.sleep(0.1)
                continue

            matches = index.lookup(*stats_tuple)
            if matches:
                human_stats = ", ".join(stat.name for stat in stats_tuple)
                print(f"[HIT] {human_stats} -> {', '.join(matches)}")
                chime()
            else:
                if LOG_DEBUG:
                    print("[INFO] No weapon match for detected stats.")

            # Print debug logs collected during read
            result_logs = getattr(driver, "_last_logs", None)
            if LOG_DEBUG and result_logs:
                for line in result_logs:
                    print(line)
                driver._last_logs = []  # reset

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Exiting...")


if __name__ == "__main__":
    idx = bootstrap_index(WEAPON_JSON)
    run_lookup_loop(idx, HOTKEY)
