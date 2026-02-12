import os
import sys
import winsound
import pywin32_system32

def _resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)

def chime():
    sound = _resource_path(os.path.join("data", "sound.wav"))
    winsound.PlaySound(sound, winsound.SND_FILENAME)
