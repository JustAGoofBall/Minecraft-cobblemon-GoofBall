#!/usr/bin/env python3
"""Build the server zip for a Modrinth modpack (.mrpack).

The zip does NOT contain the mod jars (many mods don't allow re-hosting). Instead it contains:
  - goofball-server.jar: the launcher from server-launcher/. It has the pack's server file list and
    default configs built in, downloads the mods from Modrinth on start, then starts Fabric.
  - fabric-server-launch.jar: the Fabric server launcher (downloads Minecraft + Fabric on first start)
  - everything in the repo's server/ folder (server.properties, start scripts), except server/config/:
    those files are server-only default configs and are built into goofball-server.jar instead

Needs a JDK 21+ (javac) on the PATH.

Usage:
  python3 scripts/build_server.py dist/GoofBall-Cobblemon-2.0.0.mrpack
  python3 scripts/build_server.py dist/GoofBall-Cobblemon-2.0.0.mrpack -o dist/server.zip
"""

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "server"
# Server-only default configs (not sent to players). Same rule as pack overrides: only written when missing.
SERVER_CONFIG_DIR = SERVER_DIR / "config"
LAUNCHER_SRC = REPO_ROOT / "server-launcher" / "src" / "GoofBallServer.java"
FABRIC_META = "https://meta.fabricmc.net/v2/versions"
USER_AGENT = "JustAGoofBall/Minecraft-cobblemon-GoofBall build_server.py"
LAUNCHER_JAR = "goofball-server.jar"
FABRIC_JAR = "fabric-server-launch.jar"
# Files in server/ that must stay executable inside the zip.
EXECUTABLES = {"start.sh"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def safe_path(path: str) -> str:
    """Reject absolute paths, '..' and tabs/newlines so a pack can't escape the server folder."""
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or any(c in path for c in "\t\r\n"):
        raise ValueError(f"Unsafe path in modpack: {path!r}")
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


def compile_launcher(workdir: Path) -> list[Path]:
    classes = workdir / "classes"
    subprocess.run(
        ["javac", "--release", "21", "-encoding", "UTF-8", "-d", str(classes), str(LAUNCHER_SRC)],
        check=True,
    )
    return sorted(classes.rglob("*.class"))


def build_launcher_jar(pack: zipfile.ZipFile, index: dict, workdir: Path) -> bytes:
    """Create goofball-server.jar with the server file list and default configs embedded."""
    lines = []
    for f in index["files"]:
        if f.get("env", {}).get("server") == "unsupported":
            continue
        path = safe_path(f["path"])
        lines.append("\t".join([path, f["hashes"]["sha512"], str(f["fileSize"]), *f["downloads"]]))

    # server-overrides win over overrides.
    overrides = {}
    for prefix in ("overrides/", "server-overrides/"):
        for name in pack.namelist():
            if name.startswith(prefix) and not name.endswith("/"):
                overrides[safe_path(name[len(prefix):])] = pack.read(name)
    # Server-only configs from the repo win over both.
    for src in sorted(SERVER_CONFIG_DIR.rglob("*")):
        if src.is_file():
            overrides[safe_path(src.relative_to(SERVER_DIR).as_posix())] = src.read_bytes()

    manifest = (
        "Manifest-Version: 1.0\n"
        "Main-Class: GoofBallServer\n"
        f"Class-Path: {FABRIC_JAR}\n"
        "Enable-Native-Access: ALL-UNNAMED\n"
        f"Implementation-Title: {index['name']} server launcher\n"
        f"Implementation-Version: {index['versionId']}\n"
    )
    jar_path = workdir / LAUNCHER_JAR
    with zipfile.ZipFile(jar_path, "w") as jar:
        add_bytes(jar, "META-INF/MANIFEST.MF", manifest.encode())
        classes = workdir / "classes"
        for cls in compile_launcher(workdir):
            add_bytes(jar, cls.relative_to(classes).as_posix(), cls.read_bytes())
        props = f"name={index['name']}\nversion={index['versionId']}\n"
        add_bytes(jar, "goofball/pack.properties", props.encode())
        add_bytes(jar, "goofball/files.tsv", ("\n".join(lines) + "\n").encode())
        add_bytes(jar, "goofball/overrides.txt", ("\n".join(sorted(overrides)) + "\n").encode())
        for path, data in sorted(overrides.items()):
            add_bytes(jar, f"goofball/overrides/{path}", data)
    print(f"  {LAUNCHER_JAR}: {len(lines)} server files, {len(overrides)} default config files")
    return jar_path.read_bytes()


def build(mrpack: Path, output: Path) -> None:
    with zipfile.ZipFile(mrpack) as pack, tempfile.TemporaryDirectory() as tmp:
        index = json.loads(pack.read("modrinth.index.json"))
        deps = index["dependencies"]
        mc_version = deps["minecraft"]
        loader_version = deps.get("fabric-loader")
        if not loader_version:
            sys.exit("This script only supports Fabric modpacks (no fabric-loader dependency found).")
        print(f"Pack: {index['name']} {index['versionId']} (Minecraft {mc_version}, Fabric {loader_version})")

        launcher = build_launcher_jar(pack, index, Path(tmp))
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w") as out:
            add_bytes(out, LAUNCHER_JAR, launcher)

            installer = latest_stable_installer()
            url = f"{FABRIC_META}/loader/{mc_version}/{loader_version}/{installer}/server/jar"
            add_bytes(out, FABRIC_JAR, fetch(url))
            print(f"  {FABRIC_JAR}: Fabric loader {loader_version}, installer {installer}")

            for src in sorted(SERVER_DIR.rglob("*")):
                if src.is_file() and SERVER_CONFIG_DIR not in src.parents:
                    path = src.relative_to(SERVER_DIR).as_posix()
                    add_bytes(out, path, src.read_bytes(), executable=src.name in EXECUTABLES)
                    print(f"  {path} (server/)")

    print(f"Done: {output} ({output.stat().st_size / 1_000:.0f} kB)")


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
