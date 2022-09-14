# Unzip all Raw Datas

import glob
import os, shutil
import zipfile
from tqdm import tqdm

src = os.path.join("/mnt","CarryingWearing","Zips")
target = os.path.join("/mnt","CarryingWearing","Raws")

if os.path.exists(target):
    shutil.rmtree(target)
os.mkdir(target)

for name in tqdm(sorted(glob.glob(os.path.join(src, "*.zip")))):
    with zipfile.ZipFile(name, 'r') as zip_ref:
        file = os.path.splitext(os.path.basename(name))[0]
        zip_ref.extractall(os.path.join(target, file))