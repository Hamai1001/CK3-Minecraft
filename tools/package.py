#!/usr/bin/env python3
"""Build a local developer archive, never a purported ready-to-publish release."""
from pathlib import Path
import hashlib
import json
import zipfile
import design

ROOT = Path(__file__).resolve().parents[1]


def main():
    tables=design.load()
    errors=design.preflight(tables)
    if errors: raise SystemExit('Preflight failed: '+repr(errors))
    for path,contents in design.generate(tables).items():
        if (ROOT/path).read_text(encoding='utf-8') != contents: raise SystemExit('Generated design is stale: '+path)
    jar=ROOT/'minecraft/build/libs/ckcraft-0.1.0-dev.jar'
    if not jar.is_file(): raise SystemExit('Build the Minecraft mod first')
    inputs=list((ROOT/'minecraft/src/main').rglob('*'))
    if any(p.is_file() and p.stat().st_mtime > jar.stat().st_mtime for p in inputs):
        raise SystemExit('Minecraft sources/resources changed after the JAR was built')
    files={}
    for name in ['bridge','ck3','design/sheets','docs','packaging/prism','minecraft/src','tests','tools','artifacts']:
        for p in (ROOT/name).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc':
                files[p.relative_to(ROOT).as_posix()]=p
    for name in ['README.md','MODLOG.md','AGENTS.md','.gitignore','minecraft/settings.gradle','minecraft/build.gradle','minecraft/gradle.properties','minecraft/gradlew','minecraft/gradlew.bat']:
        files[name]=ROOT/name
    files['minecraft/build/libs/ckcraft-0.1.0-dev.jar']=jar
    descriptor={
        'kind':'developer-prototype','version':'0.1.0-dev',
        'games':['crusader-kings-3','minecraft-java'],
        'testedCK3Version':None,'liveCK3RoundtripVerified':False,'oneClickVerified':False,
        'multiplayerImplemented':False,'licenseChoice':'pending','publishable':False,
        'files':{name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in sorted(files.items())}
    }
    dest=ROOT/'dist'; dest.mkdir(exist_ok=True)
    archive=dest/'CK3-Minecraft-0.1.0-dev.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zip:
        zip.writestr('DEVELOPMENT.json',json.dumps(descriptor,indent=2))
        for name,p in sorted(files.items()): zip.write(p,name)
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n')
    print('Local development archive:',archive)
    print('Bytes:',archive.stat().st_size,'SHA-256:',checksum)
    print('Not a Melty release: live CK3, automated return, portable runtime and installation still need verification.')


if __name__ == '__main__': main()
