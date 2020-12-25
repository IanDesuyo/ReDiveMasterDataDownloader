import brotli
import os
import shutil
import hashlib
import json
from datetime import datetime
import requests
import unitypack

script_dir = os.path.dirname(__file__)

header = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 XL Build/QQ3A.200805.001)"}


def main(truthVersion: str = None):
    if not truthVersion:
        truthVersion = input("TruthVersion: ")

    # Download the database if TruthVersion is exist
    r = requests.get(
        f"https://img-pc.so-net.tw/dl/Resources/{truthVersion}/Jpn/AssetBundles/Android/manifest/masterdata_assetmanifest",
        headers=header,
    )

    if r.status_code != 200:
        print(f"TruthVersion {truthVersion} is not exist")
        return
    print(f"TruthVersion {truthVersion} is exist")

    filename, path, _, size, _ = r.text.split(",")

    print(f"Downloading asset bundle ...")
    r = requests.get(f"https://img-pc.so-net.tw/dl/pool/AssetBundles/{path[:2]}/{path}", headers=header)

    if r.headers.get("Content-Length") != size:
        print("Size is not same, but it may be fine")

    with open(os.path.join(script_dir, "masterdata_master.unity3d"), "wb+") as f:
        f.write(r.content)

    masterDB = None
    # Unpack asset bundle
    with open("masterdata_master.unity3d", "rb") as f:
        bundle = unitypack.load(f)

        for asset in bundle.assets:
            for id, object in asset.objects.items():
                if object.type == "TextAsset":
                    data = object.read()
                    masterDB = data.script
                    break

    os.remove(os.path.join(script_dir, "masterdata_master.unity3d"))
    
    # Compress
    print("Compressing redive_tw.db.br ...")
    brotliDB = brotli.compress(masterDB)

    # Hash Check
    print("Generating MD5 Hash ...")
    new_hash = hashlib.md5(brotliDB).hexdigest()
    with open(os.path.join(script_dir, "out/version.json")) as f:
        old_version = json.load(f)

    if old_version.get("hash") == new_hash:
        print("Database Hash are same, Return")
        return
    print(f"Old Hash: {old_version.get('hash')} ({old_version.get('TruthVersion')})")
    print(f"New Hash: {new_hash} ({truthVersion})")

    # Save
    shutil.copyfile(os.path.join(script_dir, "out/redive_tw.db"), os.path.join(script_dir, "out/prev.redive_tw.db"))

    with open(os.path.join(script_dir, "out/redive_tw.db.br"), "wb") as f:
        f.write(brotliDB)

    with open(os.path.join(script_dir, "out/redive_tw.db"), "wb") as f:
        f.write(masterDB)

    with open(os.path.join(script_dir, "out/version.json"), "w") as f:
        json.dump({"TruthVersion": truthVersion, "hash": new_hash}, f)
        
    # Diff Check
    print("Generating diff report ...")
    os.system(
        f"{os.path.join(script_dir, 'sqldiff.exe')} {os.path.join(script_dir, 'out/prev.redive_tw.db')} {os.path.join(script_dir, 'out/redive_tw.db')} > {os.path.join(script_dir, f'out/diff/{truthVersion}.sql')}"
    )

    print("Done\n")
    return True


def guess(endAfterSucess=True, maxTry=20):
    print("Start guess TruthVersion")
    with open(os.path.join(script_dir, "out/version.json")) as f:
        old_version = json.load(f)
    lastVer = old_version.get("TruthVersion")
    print(f"Last Version: {lastVer}\n")
    big, small = int(lastVer[:5]), int(lastVer[5:]) + 1
    tryCount = 0
    while tryCount < maxTry:
        if main(f"{big:05d}{small:03d}"):
            if endAfterSucess:
                print("End guess")
                break
        if small >= 20:
            big += 1
            small = 0
        else:
            small += 1
        tryCount += 1


if __name__ == "__main__":
    guess(endAfterSucess=False)
