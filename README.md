# Endfield-Essence-Helper
Prevent sacraficing essences you need by using this!

| | | | | | | | |
|---|---|---|---|---|---|---|---|
| ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) | ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) | ![a](https://i.redd.it/q6zpzph4laig1.gif) | ![image](https://github.com/user-attachments/assets/5776565d-2a9f-4eb5-8aa6-ade3bcc2e514) |


# Usage:
Run the python script by copying the repository via

`git clone https://github.com/Geeblish/Endfield-Essence-Helper.git`

OR

![alt text]({0EEECC92-84CD-439C-852A-0CFA0CB1C336}.png)

OR

https://github.com/Geeblish/Endfield-Essence-Helper/releases/tag/Final-Releases for an executable

Then run the executable or if you downloaded the repo open your shell and run:
`./main.py`





# Requirements for python
### Make sure to run this if you are planning to run via `./main.py`
`
pip install -r requirements.txt
`
---
# Compiling
Yeah idk i just used pyinstaller
```
$site = "C:\Users\Andly\AppData\Roaming\Python\Python314\site-packages"

pyinstaller main.py `
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



