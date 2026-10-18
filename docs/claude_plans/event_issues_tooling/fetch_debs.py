"""Downloads the Debian trixie packages headless Chromium needs (plus fonts)
and unpacks them into debs/root, without root rights: resolves Depends from
the archive's Packages index and skips what dpkg says is already installed."""

import io
import lzma
import re
import subprocess
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent / "debs"
ROOT = HERE / "root"
MIRROR = "http://deb.debian.org/debian/"
WANTED = [
    "libx11-6", "libxcomposite1", "libxdamage1", "libxext6", "libxfixes3", "libxrandr2",
    "libasound2t64", "libatk1.0-0t64", "libatk-bridge2.0-0t64", "libatspi2.0-0t64",
    "libcairo2", "libcups2t64", "libdbus-1-3", "libdrm2", "libgbm1", "libglib2.0-0t64",
    "libnspr4", "libnss3", "libpango-1.0-0", "libxcb1", "libxkbcommon0",
    "fontconfig", "fonts-dejavu-core", "fonts-noto-color-emoji",
]
SKIP = {"debconf", "dpkg", "libc6", "libgcc-s1", "libstdc++6", "zlib1g", "sensible-utils", "adduser"}


def installed():
    names = set()
    for block in Path("/var/lib/dpkg/status").read_text().split("\n\n"):
        name = re.search(r"^Package: (.+)$", block, re.M)
        if name and "Status: install ok installed" in block:
            names.add(name.group(1).split(":")[0])
    return names


def index():
    data = lzma.decompress(urllib.request.urlopen(MIRROR + "dists/trixie/main/binary-amd64/Packages.xz", timeout=120).read()).decode()
    packages, provides = {}, {}
    for block in data.split("\n\n"):
        fields = dict(re.findall(r"^([\w-]+): (.*)$", block, re.M))
        if "Package" not in fields:
            continue
        packages[fields["Package"]] = fields
        for p in fields.get("Provides", "").split(","):
            if p.strip():
                provides.setdefault(p.split("(")[0].strip(), fields["Package"])
    return packages, provides


def main():
    HERE.mkdir(exist_ok=True)
    have = installed() | SKIP
    packages, provides = index()
    todo, done = list(WANTED), set()
    while todo:
        name = todo.pop()
        name = name if name in packages else provides.get(name, name)
        if name in done or name in have or name not in packages:
            continue
        done.add(name)
        for dep in re.split(r",", packages[name].get("Depends", "") + "," + packages[name].get("Pre-Depends", "")):
            first = dep.split("|")[0].split("(")[0].split(":")[0].strip()
            if first:
                todo.append(first)
    print(f"{len(done)} packages to fetch")
    for name in sorted(done):
        deb = HERE / f"{name}.deb"
        if not deb.exists():
            deb.write_bytes(urllib.request.urlopen(MIRROR + packages[name]["Filename"], timeout=300).read())
        ROOT.mkdir(exist_ok=True)
        subprocess.run(["dpkg-deb", "-x", str(deb), str(ROOT)], check=True)
    print("unpacked into", ROOT)


if __name__ == "__main__":
    main()
