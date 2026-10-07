"""Use an installed JDK 21 or fetch the official checksummed Temurin build."""
from pathlib import Path
import hashlib
import os
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.parse
import urllib.request
import zipfile

TAG = "jdk-21.0.12+8"
VERSION = "21.0.12_8"


def ensure_jdk(cache: Path):
    home = os.environ.get("JAVA_HOME")
    javac = Path(home)/"bin"/("javac.exe" if os.name == "nt" else "javac") if home else shutil.which("javac")
    if javac and Path(javac).is_file():
        result = subprocess.run([str(javac),"-version"],capture_output=True,text=True)
        if result.returncode == 0 and re.search(r"javac 21[.\s]",result.stdout+result.stderr):
            return Path(javac).resolve().parents[1]
    machine = platform.machine().lower()
    arch = {"x86_64":"x64","amd64":"x64","aarch64":"aarch64","arm64":"aarch64"}.get(machine)
    system = {"Linux":"linux","Windows":"windows","Darwin":"mac"}.get(platform.system())
    if not arch or not system:
        raise RuntimeError("Install a JDK 21 for this architecture and set JAVA_HOME")
    ext = "zip" if system == "windows" else "tar.gz"
    name = f"OpenJDK21U-jdk_{arch}_{system}_hotspot_{VERSION}.{ext}"
    base = "https://github.com/adoptium/temurin21-binaries/releases/download/"+urllib.parse.quote(TAG,safe="")+"/"
    folder = cache/"temurin21"
    binary = "javac.exe" if os.name == "nt" else "javac"
    homes = [p.parent.parent for p in folder.glob("**/bin/"+binary)] if folder.exists() else []
    if len(homes) == 1 and (folder/".verified").is_file():
        return homes[0]
    cache.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(base+name+".sha256.txt",timeout=30) as source:
        digest = source.read(1024).decode().split()[0]
    if not re.fullmatch(r"[0-9a-f]{64}",digest):
        raise RuntimeError("Official JDK checksum metadata is invalid")
    archive = cache/name
    actual = ""
    if archive.exists():
        with archive.open('rb') as stream: actual = hashlib.file_digest(stream,'sha256').hexdigest()
    if actual != digest:
        temp = archive.with_suffix(".download")
        print("Downloading official Temurin JDK 21 (checksum verification enabled).",flush=True)
        with urllib.request.urlopen(base+name,timeout=60) as source, temp.open('wb') as dest:
            while chunk := source.read(1024*1024): dest.write(chunk)
        with temp.open('rb') as stream: actual = hashlib.file_digest(stream,'sha256').hexdigest()
        if actual != digest:
            temp.unlink()
            raise RuntimeError("JDK checksum failed; download will not be used")
        temp.replace(archive)
    folder.mkdir(parents=True,exist_ok=True)
    if ext == 'zip':
        with zipfile.ZipFile(archive) as zip:
            for item in zip.infolist():
                if not (folder/item.filename).resolve().is_relative_to(folder.resolve()): raise RuntimeError("Unsafe JDK archive path")
            zip.extractall(folder)
    else:
        with tarfile.open(archive) as tar: tar.extractall(folder,filter="data")
    (folder/".verified").write_text(digest)
    homes = [p.parent.parent for p in folder.glob("**/bin/"+binary)]
    if len(homes) != 1: raise RuntimeError("JDK archive did not contain one compiler")
    return homes[0]
