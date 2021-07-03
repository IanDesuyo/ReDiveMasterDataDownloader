import brotli
import os
import shutil
import hashlib
import json
import requests
import unitypack
import logging
from logging.handlers import RotatingFileHandler

script_dir = os.path.dirname(__file__)

HEADER = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 XL Build/QQ3A.200805.001)"}

GENERATE_DIFF = os.path.exists(os.path.join(script_dir, "sqldiff.exe"))

def get(truthVersion: str = None):
    if not truthVersion:
        truthVersion = input("TruthVersion: ")

    # Download the database if TruthVersion is exist
    r = requests.get(
        f"https://img-pc.so-net.tw/dl/Resources/{truthVersion}/Jpn/AssetBundles/Android/manifest/masterdata_assetmanifest",
        headers=HEADER,
    )

    if r.status_code != 200:
        logging.info(f"TruthVersion {truthVersion} is not exist")
        return
    logging.info(f"TruthVersion {truthVersion} is exist")

    filename, path, _, size, _ = r.text.split(",")

    logging.info(f"Downloading asset bundle ...")
    r = requests.get(f"https://img-pc.so-net.tw/dl/pool/AssetBundles/{path[:2]}/{path}", headers=HEADER)

    if r.headers.get("Content-Length") != size:
        logging.info("Size is not same, but it may be fine")

    with open(os.path.join(script_dir, "masterdata_master.unity3d"), "wb+") as f:
        f.write(r.content)

    master_db = None
    # Unpack asset bundle
    with open(os.path.join(script_dir, "masterdata_master.unity3d"), "rb") as f:
        bundle = unitypack.load(f)

        for asset in bundle.assets:
            for id, object in asset.objects.items():
                if object.type == "TextAsset":
                    data = object.read()
                    master_db = data.script
                    break

    os.remove(os.path.join(script_dir, "masterdata_master.unity3d"))
    
    # Compress
    logging.info("Compressing redive_tw.db.br ...")
    brotli_db = brotli.compress(master_db)

    # Hash Check
    logging.info("Generating MD5 Hash ...")
    new_hash = hashlib.md5(brotli_db).hexdigest()
    with open(os.path.join(script_dir, "out/version.json")) as f:
        old_version = json.load(f)

    if old_version.get("hash") == new_hash:
        logging.warning("Database Hashes are same")
        return
    logging.info(f"Old Hash: {old_version.get('hash')} ({old_version.get('TruthVersion')})")
    logging.info(f"New Hash: {new_hash} ({truthVersion})")

    # Save
    shutil.copyfile(os.path.join(script_dir, "out/redive_tw.db"), os.path.join(script_dir, "out/prev.redive_tw.db"))

    with open(os.path.join(script_dir, "out/redive_tw.db.br"), "wb") as f:
        f.write(brotli_db)

    with open(os.path.join(script_dir, "out/redive_tw.db"), "wb") as f:
        f.write(master_db)

    with open(os.path.join(script_dir, "out/version.json"), "w") as f:
        json.dump({"TruthVersion": truthVersion, "hash": new_hash}, f)
        
    # Diff Check
    if GENERATE_DIFF:
        logging.info("Generating diff report ...")
        os.system(
            f"{os.path.join(script_dir, 'sqldiff.exe')} {os.path.join(script_dir, 'out/prev.redive_tw.db')} {os.path.join(script_dir, 'out/redive_tw.db')} > {os.path.join(script_dir, f'out/diff/{truthVersion}.sql')}"
        )

    logging.info("Done")
    return True


def guess(end_after_sucess=True, max_try=20):
    logging.info("Start guessing TruthVersion")
    with open(os.path.join(script_dir, "out/version.json")) as f:
        old_version = json.load(f)
    lastVer = old_version.get("TruthVersion")
    logging.info(f"Last Version: {lastVer}")
    big, small = int(lastVer[:5]), int(lastVer[6:]) + 1
    try_count = 0
    while try_count < max_try:
        if get(f"{big:05d}0{small:02d}"):
            if end_after_sucess:
                logging.info("End guess")
                break
        if small >= 20:
            big += 1
            small = 0
        else:
            small += 1
        try_count += 1


if __name__ == "__main__":
    FORMAT = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT, handlers=[RotatingFileHandler(os.path.join(script_dir, "log"), maxBytes=1*1024*1024), logging.StreamHandler()])
    
    guess(end_after_sucess=False)
