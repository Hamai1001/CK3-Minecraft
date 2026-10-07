"""Tail CK3 logs without ingesting pre-existing campaign history."""
from pathlib import Path


class LogReader:
    def __init__(self, path: Path, from_start: bool = False):
        self.path = path
        self.identity = None
        self.offset = 0
        self.buffer = b""
        self.from_start = from_start

    def read(self) -> list[str]:
        try:
            stat = self.path.stat()
            identity = (stat.st_dev,stat.st_ino)
            if self.identity is None:
                self.offset = 0 if self.from_start else stat.st_size
                self.identity = identity
            elif self.identity != identity or stat.st_size < self.offset:
                self.identity = identity
                self.offset = 0
                self.buffer = b""
            with self.path.open("rb") as stream:
                stream.seek(self.offset)
                data = stream.read(1024*1024)
                self.offset = stream.tell()
        except FileNotFoundError:
            if self.identity is None:
                # A new log created after startup has no historical contents.
                self.from_start = True
            return []
        parts = (self.buffer+data).split(b"\n")
        self.buffer = parts.pop()
        if len(self.buffer) > 65536:
            # Do not retain an unbounded/malformed log line.
            self.buffer = b""
            raise ValueError("CK3 log line exceeds protocol size")
        return [p.decode("utf-8",errors="replace") for p in parts]
