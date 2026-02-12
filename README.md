# Endfield-Essence-Helper
Prevent sacraficing essences you need by using this!

| | | | | | |
|---|---|---|---|---|---|
| ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) | ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) | ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) |

# Instructions

## Usage:
Run the python script by copying the repository via

`git clone https://github.com/Geeblish/Endfield-Essence-Helper.git`

OR

![alt text]({0EEECC92-84CD-439C-852A-0CFA0CB1C336}.png)

OR

[https://github.com/Geeblish/Endfield-Essence-Helper/releases/tag/0.1.1_Release](https://github.com/Geeblish/Endfield-Essence-Helper/releases/tag/0.1.1_Release) for an executable

Then run the executable or if you downloaded the repo open your shell and run:
`./main.py`

or open
`./EndfieldEssenceHelper.exe`

## Make sure your game is in 1920x1080


# Requirements for python
### Make sure to run this if you are planning to run via `./main.py`
`
python -m pip install -r requirements.txt
`

# Configs
## To mess with different configs, go in [main.py](https://github.com/Geeblish/Endfield-Essence-Helper/blob/main/main.py) or [lookup_driver.py](https://github.com/Geeblish/Endfield-Essence-Helper/blob/main/lookup_driver.py) and change them in file. 
```
WEAPON_JSON = Path("data") / "weapons.json"
HOTKEY = "f10"  # user-changeable toggle
LOG_DEBUG = False  # verbose logging toggle
SAVE_IMAGES = False  # set True when you need dumps in data/tmp/ocr_debug
GUARD_MODE = GuardMode.IMAGE  # IMAGE | OCR | NONE
USE_STAT_CACHE = True        # use cache lookups
CREATE_STAT_CACHE = False     # if True, save matched stat images to data/matched
USE_QUALITY_GUARD = False     # set False to skip gold pixel check (e.g., to see lower rarity)
REQUIRE_THREE_STATS = True    # require all 3 stats before lookup
```
> [!caution]
> ## THERE WILL NOT BE (at least my release) A CONFIG FILE FOR THE EXECUTABLE VERSION.
> ## I AM TOO LAZY TO MAKE A CONFIG FILE. ALSO I AM TOO LAZY TO FIX SOMETHING IF THE USER BREAKS IT
> <sub>That being said, I know the executable is buggy so I wont be helping with that either 🫣 </sub>

> [!note]
> The executable is shipped with image matching, using ./data/matches as the lookup

---
# Compiling
Yeah idk i just used pyinstaller
```
$site = "C:\Users\Andly\AppData\Roaming\Python\Python314\site-packages"

pythom -m PyInstaller main.py `
  --onefile `
  --name EndfieldEssenceHelper `
  --hidden-import pyclipper `
  --hidden-import six `
  --collect-all rapidocr_onnxruntime `
  --add-data "data;data" `
  --add-data "$site\rapidocr_onnxruntime\config.yaml;rapidocr_onnxruntime" `
  --add-data "$site\rapidocr_onnxruntime\models;rapidocr_onnxruntime\models" `
  --add-data "$site\rapidocr_onnxruntime\ch_ppocr_v3_det;rapidocr_onnxruntime\ch_ppocr_v3_det" `
  --add-data "$site\rapidocr_onnxruntime\ch_ppocr_v3_rec;rapidocr_onnxruntime\ch_ppocr_v3_rec" `
  --add-data "$site\rapidocr_onnxruntime\ch_ppocr_v2_cls;rapidocr_onnxruntime\ch_ppocr_v2_cls" `
  --add-data "Essence_Helper.py;." `
  --add-data "audio_helper.py;." `
  --add-data "lookup_driver.py;." `
  --add-data "mappings.py;." `
  --add-data "setup.py;." `
  --add-data "main.py;."

```

Emojis for AI filtering

🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫃🫣🫃🫃🫃🫃🫃🫃






