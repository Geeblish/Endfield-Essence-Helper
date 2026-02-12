from __future__ import annotations

import cv2
import mss
import numpy as np
import win32gui  # type: ignore
from difflib import SequenceMatcher
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple, Union
from enum import Enum

from rapidocr_onnxruntime import RapidOCR


from Essence_Helper import Stat
from mappings import STAT1_MAPPING, STAT2_MAPPING, STAT3_MAPPING

# ---- Configuration ---------------------------------------------------------

WINDOW_TITLE = "Endfield"

QUALITY_COLOR = (255, 186, 3)  # #ffba03
COLOR_TOLERANCE = 10
def resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel


DEBUG_DIR = Path("data/tmp/ocr_debug")
MATCHED_DIR = Path("data/matched")

MENU_TEMPLATES = {
    "inventory": resource_path("data/Menu_Guard_Inventory.png"),
    "etch": resource_path("data/Menu_Guard_Etch.png"),
}

# Lightweight signature params for guard hashing
GUARD_SIG_SIZE = 16  # resize to 16x16
GUARD_HAMMING_THRESH = 40  # max differing bits (of 256) to accept
STAT_HAMMING_THRESH = 40
STAT_HAMMING_STRICT = 12
STAT_HAMMING_MARGIN = 8  # best must beat runner-up by this to accept loose match
STAT_CONTRAST_MIN = 25  # skip OCR when text is still fading (low contrast)

class GuardMode(Enum):
    NONE = "none"
    OCR = "ocr"
    IMAGE = "image"

LAYOUTS = [
    {
        "name": "inventory",
        "regions": [
            {"x": 0.025, "y": 0.072, "w": 0.05, "h": 0.023},  # menu guard
            {"x": 0.785, "y": 0.337, "w": 0.16, "h": 0.023},  # stat 1
            {"x": 0.785, "y": 0.387, "w": 0.16, "h": 0.023},  # stat 2
            {"x": 0.785, "y": 0.44, "w": 0.16, "h": 0.023},   # stat 3
            {"x": 0.789, "y": 0.075, "w": 0.001, "h": 0.001},  # quality pixel
        ],
        "menu_idx": 0,
        "quality_idx": 4,
        "stat_indices": [1, 2, 3],
        "template_key": "inventory",
    },
    {
        "name": "etch",
        "regions": [
            {"x": 0.035, "y": 0.03, "w": 0.09, "h": 0.023},   # menu guard
            {"x": 0.1, "y": 0.50, "w": 0.15, "h": 0.023},     # stat 1
            {"x": 0.1, "y": 0.54, "w": 0.15, "h": 0.023},     # stat 2
            {"x": 0.1, "y": 0.575, "w": 0.15, "h": 0.023},    # stat 3
        ],
        "menu_idx": 0,
        "quality_idx": None,  # no dedicated quality pixel in this layout
        "stat_indices": [1, 2, 3],
        "template_key": "etch",
    },
]


# ---- Utility helpers ------------------------------------------------------

def _get_game_rect(window_title: str = WINDOW_TITLE) -> Dict[str, int]:
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise RuntimeError("Game window not found")

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])

    return {
        "left": left,
        "top": top,
        "width": right - left,
        "height": bottom - top,
    }


def _norm_to_abs(region: Dict[str, float], win: Dict[str, int]) -> Dict[str, int]:
    return {
        "left": int(win["left"] + region["x"] * win["width"]),
        "top": int(win["top"] + region["y"] * win["height"]),
        "width": int(region["w"] * win["width"]),
        "height": int(region["h"] * win["height"]),
    }


def _grab_region(rect: Dict[str, int]) -> np.ndarray:
    """
    Grab a region with a fresh mss instance to avoid thread-local handle issues
    seen in some PyInstaller builds.
    """
    for _ in range(2):  # retry once on rare handle errors
        try:
            with mss.mss() as sct:
                grab = sct.grab(rect)  # BGRA
                arr = np.frombuffer(grab.bgra, dtype=np.uint8).reshape((grab.height, grab.width, 4))
                return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        except AttributeError:
            continue
    # If it still fails, raise to surface the issue
    with mss.mss() as sct:
        grab = sct.grab(rect)
        arr = np.frombuffer(grab.bgra, dtype=np.uint8).reshape((grab.height, grab.width, 4))
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)


def _preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    # img is BGR
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    scale = 3 if min(h, w) < 120 else 2
    gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _normalize(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace()).strip()


def _pixel_matches(img: np.ndarray, target: Tuple[int, int, int], tolerance: int) -> bool:
    b, g, r = img[0, 0, :3].astype(int)
    return all(abs(c - t) <= tolerance for c, t in zip((r, g, b), target))


def _signature(img_gray: np.ndarray) -> np.ndarray:
    resized = cv2.resize(img_gray, (GUARD_SIG_SIZE, GUARD_SIG_SIZE), interpolation=cv2.INTER_AREA)
    thresh = resized.mean()
    bits = (resized >= thresh).astype(np.uint8)
    return np.packbits(bits.reshape(-1))


def _hamming(sig1: np.ndarray, sig2: np.ndarray) -> int:
    return int(np.unpackbits(np.bitwise_xor(sig1, sig2)).sum())


def _low_contrast(img: np.ndarray, threshold: float = STAT_CONTRAST_MIN) -> bool:
    # img is BGR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(gray.std()) < threshold


def _choose_stat(
    text: str,
    mapping: Dict[str, Sequence[str] | str],
    threshold: float = 0.90,
    margin: float = 0.07,
) -> Optional[Stat]:
    if not text:
        return None

    norm_text = _normalize(text)
    best: Optional[Tuple[Stat, float]] = None
    second: Optional[Tuple[Stat, float]] = None

    for key, values in mapping.items():
        opts = values if isinstance(values, list) else [values]
        for opt in opts:
            norm_opt = _normalize(opt)
            if norm_text == norm_opt:
                return Stat[key]

            score = SequenceMatcher(None, norm_text, norm_opt).ratio()
            if best is None or score > best[1]:
                second = best
                best = (Stat[key], score)
            elif second is None or score > second[1]:
                second = (Stat[key], score)

    if best and best[1] >= threshold:
        if second is None or (best[1] - second[1] >= margin):
            return best[0]
    return None


# ---- Public driver --------------------------------------------------------

class LookupDriver:
    def __init__(
        self,
        window_title: str = WINDOW_TITLE,
        save_images: bool = False,
        log_debug: bool = False,
        guard_mode: GuardMode = GuardMode.IMAGE,
        use_stat_cache: bool = False,
        create_stat_cache: bool = False,
        require_three_stats: bool = True,
    ):
        self.window_title = window_title
        self.save_images = save_images
        self.log_debug = log_debug
        self.guard_mode = guard_mode
        self.use_stat_cache = use_stat_cache
        self.create_stat_cache = create_stat_cache
        self.require_three_stats = require_three_stats
        self.ocr = RapidOCR()
        self._last_logs: List[str] = []
        self._debug_counter = 0
        self._templates: Dict[str, Optional[np.ndarray]] = {}
        self._template_sigs: Dict[str, Optional[np.ndarray]] = {}
        self._stat_templates: Dict[str, np.ndarray] = {}
        self._stat_sigs: Dict[str, np.ndarray] = {}
        for key, path in MENU_TEMPLATES.items():
            if path.exists():
                self._templates[key] = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                self._template_sigs[key] = self._make_signature(self._templates[key])
            else:
                self._templates[key] = None
                self._template_sigs[key] = None

        self._load_stat_cache()

    def _make_signature(self, tpl_gray: np.ndarray) -> np.ndarray:
        return _signature(tpl_gray)

    def _load_stat_cache(self) -> None:
        MATCHED_DIR.mkdir(parents=True, exist_ok=True)
        for path in MATCHED_DIR.glob("*.png"):
            stat_name = path.stem
            try:
                Stat[stat_name]  # validate
            except KeyError:
                continue
            gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                continue
            self._stat_templates[stat_name] = gray
            self._stat_sigs[stat_name] = _signature(gray)

    def _capture_region(self, layout: Dict, idx: int, win: Optional[Dict[str, int]] = None) -> np.ndarray:
        win = win or _get_game_rect(self.window_title)
        rect = _norm_to_abs(layout["regions"][idx], win)
        return _grab_region(rect)

    def _capture_all(self, layout: Dict, win: Optional[Dict[str, int]] = None) -> List[np.ndarray]:
        win = win or _get_game_rect(self.window_title)
        abs_regions = [_norm_to_abs(r, win) for r in layout["regions"]]
        return [_grab_region(rect) for rect in abs_regions]

    def _ocr_text(self, img: np.ndarray) -> str:
        processed = _preprocess_for_ocr(img)
        result, _ = self.ocr(processed)

        if not result:
            return ""

        # result can be list of [bbox, text, score] or [text, score, box]; be defensive
        best_text = ""
        best_score = -1.0
        for item in result:
            if isinstance(item, (list, tuple)):
                # common layouts: [bbox, text, score] or [text, score]
                if len(item) >= 3 and isinstance(item[1], str):
                    text, score = item[1], float(item[2])
                elif len(item) >= 2 and isinstance(item[0], str):
                    text, score = item[0], float(item[1])
                else:
                    continue
            else:
                continue

            if score > best_score:
                best_score = score
                best_text = text

        return best_text.strip()

    def _check_menu_guard(self, layout: Dict, img: np.ndarray) -> bool:
        if self.guard_mode == GuardMode.NONE:
            self._last_guard_text = ""
            return True

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        tpl = self._templates.get(layout["template_key"])
        tpl_sig = self._template_sigs.get(layout["template_key"])

        if self.guard_mode == GuardMode.IMAGE:
            if tpl_sig is not None:
                sig = _signature(gray)
                dist = _hamming(sig, tpl_sig)
                if dist <= GUARD_HAMMING_THRESH:
                    return True

            if tpl is not None:
                res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
                if res.size > 0 and res.max() >= 0.6:
                    return True
            return False

        # OCR-only guard detection
        text = self._ocr_text(img).lower()
        self._last_guard_text = text  # debug
        if "essence" not in text:
            return False

        if layout["name"] == "inventory":
            return True  # "essence" is enough
        if layout["name"] == "etch":
            return "etch essence" in text or "essence" in text
        return True

    def _stat_from_cache(self, img: np.ndarray) -> Optional[Stat]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sig = _signature(gray)
        best: Tuple[str, int] | None = None
        second_best: Tuple[str, int] | None = None
        for stat_name, tpl_sig in self._stat_sigs.items():
            dist = _hamming(sig, tpl_sig)
            if best is None or dist < best[1]:
                second_best = best
                best = (stat_name, dist)
            elif second_best is None or dist < second_best[1]:
                second_best = (stat_name, dist)

        if best is None:
            return None

        # Strict accept
        if best[1] <= STAT_HAMMING_STRICT:
            return Stat[best[0]]

        # Margin accept
        runner = second_best[1] if second_best else 256
        if best[1] <= STAT_HAMMING_THRESH and (runner - best[1] >= STAT_HAMMING_MARGIN):
            return Stat[best[0]]

        return None

    def _persist_stat_template(self, stat: Stat, img: np.ndarray) -> None:
        name = stat.name
        path = MATCHED_DIR / f"{name}.png"
        if path.exists():
            return
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(str(path), gray)
        self._stat_templates[name] = gray
        self._stat_sigs[name] = _signature(gray)

    def read(self) -> Dict[str, object]:
        t0 = time.perf_counter()
        win = _get_game_rect(self.window_title)

        logs: List[str] = []
        chosen_layout = None
        menu_img_cache: Optional[np.ndarray] = None

        # Try layouts in order; release unneeded images ASAP
        for layout in LAYOUTS:
            menu_img = self._capture_region(layout, layout["menu_idx"], win)
            menu_ok = self._check_menu_guard(layout, menu_img)
            if menu_ok:
                chosen_layout = layout
                menu_img_cache = menu_img
                if self.log_debug:
                    logs.append(f"[HIT] Menu Guard detected: {layout['name']} menu")
                break
            else:
                if self.save_images or self.log_debug:
                    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
                    fname = DEBUG_DIR / f"guard_{layout['name']}_{self._debug_counter}.png"
                    cv2.imwrite(str(fname), menu_img)
                del menu_img
                if self.log_debug:
                    logs.append(f"[MISS] Guard OCR '{getattr(self,'_last_guard_text','')}' for layout {layout['name']}")
                self._debug_counter += 1

        if chosen_layout is None:
            self._last_logs = logs
            return {"quality_ok": False, "menu_ok": False, "logs": logs, "menu_text": "", "raw_texts": ["", "", ""], "stats": [None, None, None]}

        # Capture all regions in one shot to keep stat lines in sync
        t_cap = time.perf_counter()
        imgs = self._capture_all(chosen_layout, win)
        t_after_cap = time.perf_counter()

        if self.save_images:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)
            for i, img in enumerate(imgs):
                cv2.imwrite(str(DEBUG_DIR / f"{chosen_layout['name']}_region_{i}.png"), img)

        quality_ok = True
        if chosen_layout["quality_idx"] is not None and getattr(self, "use_quality_guard", True):
            qimg = imgs[chosen_layout["quality_idx"]]
            quality_ok = _pixel_matches(qimg, QUALITY_COLOR, COLOR_TOLERANCE)
            if quality_ok and self.log_debug:
                logs.append("[HIT] Quality pixel matches #ffba03")
            if not quality_ok:
                self._last_logs = logs
                return {"quality_ok": False, "menu_ok": True, "logs": logs, "menu_text": "", "raw_texts": ["", "", ""], "stats": [None, None, None]}

        menu_text = ""
        if self.save_images:
            menu_img_src = menu_img_cache if menu_img_cache is not None else imgs[chosen_layout["menu_idx"]]
            menu_text = self._ocr_text(menu_img_src)

        raw_texts: List[str] = ["", "", ""]
        stats: List[Optional[Stat]] = [None, None, None]
        from_cache: List[bool] = [False, False, False]
        low_contrast_flags: List[bool] = [False, False, False]

        for idx_out, region_idx in enumerate(chosen_layout["stat_indices"]):
            region_img = imgs[region_idx]

            if _low_contrast(region_img):
                if self.log_debug:
                    logs.append(f"[SKIP] Stat region {idx_out+1} low contrast (fading)")
                stats[idx_out] = None
                raw_texts[idx_out] = ""
                low_contrast_flags[idx_out] = True
                continue

            # Fast cache lookup
            if self.use_stat_cache:
                cached_stat = self._stat_from_cache(region_img)
                if cached_stat:
                    stats[idx_out] = cached_stat
                    raw_texts[idx_out] = cached_stat.name
                    from_cache[idx_out] = True
                    continue

            raw = self._ocr_text(region_img)
            raw_texts[idx_out] = raw
            stats[idx_out] = _choose_stat(raw, STAT_MAPPING := STAT1_MAPPING)  # mappings all unified

            if stats[idx_out] and self.create_stat_cache:
                self._persist_stat_template(stats[idx_out], region_img)

        # If any duplicates or None, fall back to OCR-only for those slots to avoid stale cache
        seen = set()
        for idx, stat in enumerate(stats):
            if stat is None or stat in seen:
                if _low_contrast(imgs[chosen_layout["stat_indices"][idx]]):
                    if self.log_debug:
                        logs.append(f"[SKIP] Stat region {idx+1} low contrast (refetch)")
                    stats[idx] = None
                    raw_texts[idx] = ""
                    continue
                raw = self._ocr_text(imgs[chosen_layout["stat_indices"][idx]])
                raw_texts[idx] = raw
                stats[idx] = _choose_stat(raw, STAT_MAPPING := STAT1_MAPPING)
                from_cache[idx] = False
                low_contrast_flags[idx] = False
            if stats[idx]:
                seen.add(stats[idx])

        if not self.save_images:
            # release captured images promptly
            del imgs

        if self.log_debug:
            t_end = time.perf_counter()
            logs.append(
                "[TIMING] menu_check={:.1f}ms capture={:.1f}ms ocr={:.1f}ms total={:.1f}ms".format(
                    (t_cap - t0) * 1000,
                    (t_after_cap - t_cap) * 1000,
                    (t_end - t_after_cap) * 1000,
                    (t_end - t0) * 1000,
                )
            )

        self._last_logs = logs
        return {
            "quality_ok": quality_ok,
            "menu_ok": True,
            "menu_text": menu_text,
            "raw_texts": raw_texts,
            "stats": stats,
            "logs": logs,
            "layout": chosen_layout["name"],
        }

    def stat_tuple(self) -> Optional[Union[Tuple[Stat, Stat], Tuple[Stat, Stat, Stat]]]:
        result = self.read()
        if not result["quality_ok"]:
            return None

        stats: List[Optional[Stat]] = result["stats"]  # type: ignore[assignment]
        present = [s for s in stats if s is not None]

        if self.require_three_stats:
            if len(present) == 3:
                return present[0], present[1], present[2]
            return None

        if len(present) == 3:
            return present[0], present[1], present[2]
        if len(present) == 2:
            return present[0], present[1]
        return None


if __name__ == "__main__":
    driver = LookupDriver(save_debug=True)
    info = driver.read()
    print(info)
