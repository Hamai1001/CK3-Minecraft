#!/usr/bin/env python3
"""Install only our native CK3 mod into an explicitly selected Documents folder."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def install(documents: Path):
    source = ROOT/"ck3"/"ckcraft"
    mods = documents/"Paradox Interactive"/"Crusader Kings III"/"mod"
    target = mods/"ckcraft_dev"
    descriptor = mods/"ckcraft_dev.mod"
    if target.is_symlink() or descriptor.is_symlink():
        raise RuntimeError("Refusing to follow existing mod installation symlinks")
    manifest = target/".ckcraft-install.json"
    payload = {p.relative_to(source).as_posix():p for p in source.rglob('*') if p.is_file()}
    hashes = {name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in payload.items()}
    old = json.loads(manifest.read_text()) if manifest.is_file() else None
    if target.exists() and old is None:
        raise RuntimeError("Existing mod folder has no CKCraft ownership manifest; nothing was overwritten")
    if old:
        actual_files = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}-{".ckcraft-install.json"}
        if actual_files != set(old['files']):
            raise RuntimeError("Installed mod contains added/missing user files; nothing was overwritten")
        for name,digest in old['files'].items():
            path = target/name
            if not path.resolve().is_relative_to(target.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError("Installed mod was edited; preserve those edits before refreshing")
        if descriptor.is_file() and hashlib.sha256(descriptor.read_bytes()).hexdigest() != old['descriptor']:
            raise RuntimeError("Mod descriptor was edited; nothing was overwritten")
    elif descriptor.exists():
        raise RuntimeError("Existing descriptor belongs to another installation")
    text = source.joinpath('descriptor.mod').read_text()+f'\npath="{target.resolve().as_posix()}"\n'
    target.mkdir(parents=True,exist_ok=True)
    for name,p in payload.items():
        dest = target/name
        if dest.is_symlink(): raise RuntimeError("Refusing to follow installed mod symlinks")
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
    if old:
        for name in set(old['files'])-set(payload): (target/name).unlink()
    descriptor.write_text(text,encoding='utf-8')
    manifest.write_text(json.dumps({'files':hashes,'descriptor':hashlib.sha256(descriptor.read_bytes()).hexdigest()},indent=2))
    return target


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--documents',type=Path,required=True,help='Actual Windows Documents folder (can be OneDrive Documents)')
    args=parser.parse_args()
    print('Installed development mod:',install(args.documents))
