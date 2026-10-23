"""Build clean QGIS ZIPs from the plugin, excluding caches and AppleDouble files."""

import argparse
import configparser
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "qhardcharger"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", metavar="PLATFORM")
    args = parser.parse_args()
    metadata = configparser.ConfigParser()
    metadata.read(PLUGIN / "metadata.txt")
    version = metadata["general"]["version"]
    tag = os.environ.get("GITHUB_REF", "")
    if tag.startswith("refs/tags/v") and tag.removeprefix("refs/tags/v") != version:
        raise ValueError("Release tag must match metadata.txt version")
    if metadata["general"].getboolean("experimental"):
        raise ValueError("Hardcharger releases must be stable")
    if args.offline and sys.platform == "darwin":
        # QGIS's hardened runtime loads the ad-hoc-signed native dependencies.
        for pattern in ("*.so", "*.dylib"):
            for path in (PLUGIN / "embedded_external_libs").rglob(pattern):
                subprocess.run(["/usr/bin/codesign", "--force", "--sign", "-", str(path)],
                               check=True, capture_output=True)
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    suffix = f"-offline-{args.offline}-py{sys.version_info.major}{sys.version_info.minor}" if args.offline else ""
    archive = out / f"qhardcharger-{version}{suffix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "LICENSE", "qhardcharger/LICENSE")
        for path in sorted(PLUGIN.rglob("*")):
            if not path.is_file() or path.name == "LICENSE":
                continue
            if any(part in ("__pycache__", ".DS_Store", "__MACOSX") or part.startswith("._")
                   for part in path.parts) or path.suffix in (".pyc", ".pyo"):
                continue
            if not args.offline and "embedded_external_libs" in path.parts:
                continue
            z.write(path, path.relative_to(ROOT))
    if not args.offline:
        shutil.copyfile(archive, out / "qhardcharger.zip")
        if archive.stat().st_size >= 25 * 1024 * 1024:
            raise ValueError("Slim package exceeds QGIS repository upload limit")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("Invalid archive")
    print(f"Built {archive.name} ({archive.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
