import os
import winsound
import pywin32_system32

def chime():
    sound = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data","sound.wav")
    winsound.PlaySound(sound, winsound.SND_FILENAME)
