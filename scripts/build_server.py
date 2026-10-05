#!/usr/bin/env python3
"""Build a ready-to-run server zip from a Modrinth modpack (.mrpack).

The zip contains:
  - every file from the .mrpack that the server needs (env.server != "unsupported"),
    downloaded and checked against its sha512 hash
  - the mrpack's overrides/ and server-overrides/ folders
  - everything in the repo's server/ folder (server.properties, start scripts)
  - the Fabric server launcher as fabric-server-launch.jar

Usage:
  python3 scripts/build_server.py dist/GoofBall-Cobblemon-1.0.0.mrpack
  python3 scripts/build_server.py dist/GoofBall-Cobblemon-1.0.0.mrpack -o dist/server.zip
"""

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "server"
FABRIC_META = "https://meta.fabricmc.net/v2/versions"
USER_AGENT = "JustAGoofBall/Minecraft-cobblemon-GoofBall build_server.py"
LAUNCHER_NAME = "fabric-server-launch.jar"
# Files in server/ that must stay executable inside the zip.
EXECUTABLES = {"start.sh"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def safe_path(path: str) -> str:
    """Reject absolute paths and '..' so a pack can't write outside the zip root."""
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"Unsafe path in modpack: {path}")
    return str(p)


def latest_stable_installer() -> str:
    installers = json.loads(fetch(f"{FABRIC_META}/installer"))
    return next(i["version"] for i in installers if i["stable"])


def add_bytes(out: zipfile.ZipFile, name: str, data: bytes, executable: bool = False) -> None:
    info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    # Regular file (0o100000) + permissions, so unzip and Crafty keep start.sh executable.
    info.external_attr = (0o100000 | (0o755 if executable else 0o644)) << 16
    out.writestr(info, data)


def build(mrpack: Path, output: Path) -> None:
    with zipfile.ZipFile(mrpack) as pack:
        index = json.loads(pack.read("modrinth.index.json"))
        deps = index["dependencies"]
        mc_version = deps["minecraft"]
        loader_version = deps.get("fabric-loader")
        if not loader_version:
            sys.exit("This script only supports Fabric modpacks (no fabric-loader dependency found).")

        print(f"Pack: {index['name']} {index['versionId']} (Minecraft {mc_version}, Fabric {loader_version})")
        output.parent.mkdir(parents=True, exist_ok=True)
        written = set()

        with zipfile.ZipFile(output, "w") as out:
            # 1. Mods and other downloaded files.
            for f in index["files"]:
                path = safe_path(f["path"])
                if f.get("env", {}).get("server") == "unsupported":
                    print(f"  skip (client only) {path}")
                    continue
                data = None
                for url in f["downloads"]:
                    try:
                        data = fetch(url)
                        break
                    except OSError as e:
                        print(f"  download failed ({e}), trying next mirror: {url}")
                if data is None:
                    sys.exit(f"Could not download {path}")
                if hashlib.sha512(data).hexdigest() != f["hashes"]["sha512"]:
                    sys.exit(f"sha512 mismatch for {path}")
                add_bytes(out, path, data)
                written.add(path)
                print(f"  add  {path}")

            # 2. Overrides: server-overrides win over overrides.
            overrides = {}
            for prefix in ("overrides/", "server-overrides/"):
                for name in pack.namelist():
                    if name.startswith(prefix) and not name.endswith("/"):
                        overrides[safe_path(name[len(prefix):])] = name
            for path, name in sorted(overrides.items()):
                add_bytes(out, path, pack.read(name))
                written.add(path)
                print(f"  add  {path} (override)")

            # 3. Repo server/ folder (server.properties, start scripts).
            for src in sorted(SERVER_DIR.rglob("*")):
                if src.is_file():
                    path = src.relative_to(SERVER_DIR).as_posix()
                    if path in written:
                        sys.exit(f"{path} exists both in the modpack and in server/")
                    add_bytes(out, path, src.read_bytes(), executable=src.name in EXECUTABLES)
                    print(f"  add  {path} (server/)")

            # 4. Fabric server launcher.
            installer = latest_stable_installer()
            url = f"{FABRIC_META}/loader/{mc_version}/{loader_version}/{installer}/server/jar"
            add_bytes(out, LAUNCHER_NAME, fetch(url))
            print(f"  add  {LAUNCHER_NAME} (Fabric loader {loader_version}, installer {installer})")

    print(f"Done: {output} ({output.stat().st_size / 1_000_000:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mrpack", type=Path, help="path to the .mrpack file")
    parser.add_argument("-o", "--output", type=Path, help="output zip (default: <mrpack name>-Server.zip next to it)")
    args = parser.parse_args()

    output = args.output
    if output is None:
        stem = args.mrpack.stem
        name = stem.replace("GoofBall-Cobblemon-", "GoofBall-Cobblemon-Server-", 1)
        if name == stem:
            name = f"{stem}-server"
        output = args.mrpack.with_name(f"{name}.zip")
    build(args.mrpack, output)


if __name__ == "__main__":
    main()
