#!/usr/bin/env python3
"""Small pinned Gradle bootstrap; validates the official distribution SHA-256."""
from pathlib import Path
import hashlib
import os
import platform
import subprocess
import sys
import urllib.request
import urllib.parse
import zipfile
from java import ensure_jdk

VERSION = "8.10.2"
SHA256 = "31c55713e40233a8303827ceb42ca48a47267a0ad4bab9177123121e71524c26"
ROOT = Path(__file__).resolve().parents[1]


def main():
    os.environ.setdefault("GRADLE_USER_HOME",str(ROOT/".gradle"/"user"))
    cache = Path(os.environ.get("CKCRAFT_TOOL_CACHE",ROOT/".gradle"/"tools"))
    cache.mkdir(parents=True,exist_ok=True)
    java_home = ensure_jdk(cache)
    os.environ["JAVA_HOME"] = str(java_home)
    os.environ["PATH"] = str(java_home/"bin")+os.pathsep+os.environ.get("PATH","")
    folder = cache/f"gradle-{VERSION}"
    stamp = folder/".ckcraft-verified"
    if not stamp.is_file() or stamp.read_text() != SHA256:
        archive = cache/f"gradle-{VERSION}-bin.zip"
        if not archive.is_file() or hashlib.file_digest(archive.open('rb'),'sha256').hexdigest() != SHA256:
            tmp = archive.with_suffix('.tmp')
            with urllib.request.urlopen(f"https://downloads.gradle.org/distributions/gradle-{VERSION}-bin.zip",timeout=60) as source, tmp.open('wb') as dest:
                while chunk := source.read(1024*1024):
                    dest.write(chunk)
            with tmp.open('rb') as stream:
                actual = hashlib.file_digest(stream,'sha256').hexdigest()
            if actual != SHA256:
                tmp.unlink()
                raise SystemExit("Gradle checksum failed; refusing to use the download")
            tmp.replace(archive)
        with zipfile.ZipFile(archive) as zip:
            for entry in zip.infolist():
                if not (cache/entry.filename).resolve().is_relative_to(cache.resolve()):
                    raise SystemExit("Invalid Gradle archive path")
            zip.extractall(cache)
        stamp.write_text(SHA256)
    executable = folder/"bin"/("gradle.bat" if os.name == 'nt' else "gradle")
    if os.name != 'nt':
        executable.chmod(0o755)
    options = []
    truststore = os.environ.get('CKCRAFT_JAVA_TRUSTSTORE')
    if not truststore and platform.system() == 'Linux' and Path('/etc/ssl/certs/java/cacerts').is_file():
        # Temurin's bundled roots do not include the cloud's managed proxy CA.
        # Reuse the existing system truststore; TLS verification stays enabled.
        truststore = '/etc/ssl/certs/java/cacerts'
    if truststore:
        if not Path(truststore).is_file(): raise SystemExit('Configured JVM truststore is missing')
        options += ['-Djavax.net.ssl.trustStore='+truststore]
    # Java does not consume HTTPS_PROXY automatically. Reuse the cloud's proxy,
    # without exposing or copying any proxy authentication.
    proxies = urllib.request.getproxies()
    proxy = proxies.get('https') or proxies.get('http')
    if proxy:
        parsed = urllib.parse.urlsplit(proxy)
        if parsed.username or parsed.password:
            raise SystemExit("Authenticated proxy requires supported JVM credential injection")
        if parsed.hostname:
            for scheme in ('http','https'):
                options += [f'-D{scheme}.proxyHost={parsed.hostname}',f'-D{scheme}.proxyPort={parsed.port or 80}']
            options += ['-Dhttp.nonProxyHosts=localhost|127.*|[::1]']
    return subprocess.call([str(executable),*options,'-p',str(ROOT/'minecraft'),*sys.argv[1:]])


if __name__ == '__main__':
    sys.exit(main())
