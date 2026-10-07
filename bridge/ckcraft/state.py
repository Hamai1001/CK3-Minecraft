"""Durable single-flight state machine; COMPLETE means CK3 acknowledged."""
from dataclasses import asdict
from pathlib import Path
import json
import sqlite3
import threading
import time

from .protocol import Request, Ack
from .return_command import command


class Conflict(ValueError):
    pass


class State:
    def __init__(self, directory: Path, campaign: str, design: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.campaign = campaign
        self.lock = threading.RLock()
        self.db = sqlite3.connect(directory / "sessions.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, campaign TEXT, request TEXT, status TEXT, player TEXT, instance TEXT, outcome TEXT, updated REAL)")
        self.db.commit()
        self.scenarios = {r["id"]: r for r in json.loads((design / "scenarios.json").read_text())["rows"]}
        self.outcomes = {r["id"]: r for r in json.loads((design / "outcomes.json").read_text())["rows"]}

    def close(self):
        self.db.close()

    def _current(self):
        return self.db.execute("SELECT * FROM sessions WHERE campaign=? AND status!='COMPLETE' ORDER BY updated LIMIT 1", (self.campaign,)).fetchone()

    def snapshot(self):
        with self.lock:
            row = self._current()
            if row is None:
                return {"protocol": 1, "session": None}
            data = dict(row)
            request = json.loads(data.pop("request"))
            data.pop("campaign")
            return {"protocol": 1, "session": {**data, **request, "design": self.scenarios[request["scenario"]]}}

    def accept(self, request: Request) -> bool:
        with self.lock:
            key = request.identity(self.campaign)
            existing = self.db.execute("SELECT request FROM sessions WHERE id=?", (key,)).fetchone()
            if existing:
                if json.loads(existing["request"]) != asdict(request):
                    raise Conflict("sequence reused with different content; use an isolated campaign state directory")
                return False
            if self._current() is not None:
                raise Conflict("another CK3 event is pending; no event was overwritten")
            self.db.execute("INSERT INTO sessions VALUES(?,?,?,'WAITING',NULL,NULL,NULL,?)", (key,self.campaign,json.dumps(asdict(request)),time.time()))
            self.db.commit()
            return True

    def claim(self, key: str, player: str, instance: str):
        with self.lock:
            row = self._current()
            if row is None or row["id"] != key:
                raise Conflict("unknown or stale session")
            if row["status"] == "ACTIVE" and row["player"] == player and row["instance"] == instance:
                return self.snapshot()
            if row["status"] != "WAITING":
                raise Conflict("session already owned or awaiting CK3 acknowledgement")
            self.db.execute("UPDATE sessions SET status='ACTIVE',player=?,instance=?,updated=? WHERE id=?", (player,instance,time.time(),key))
            self.db.commit()
            return self.snapshot()

    def result(self, key: str, player: str, instance: str, outcome: str):
        with self.lock:
            completed = self.db.execute("SELECT * FROM sessions WHERE id=? AND campaign=? AND status='COMPLETE'",(key,self.campaign)).fetchone()
            if completed and completed['player'] == player and completed['instance'] == instance:
                request = Request(**json.loads(completed['request']))
                scenario = self.scenarios[request.scenario]
                if outcome not in {scenario['won'],scenario['lost'],scenario['aborted']}:
                    raise Conflict('invalid late result')
                # CK3 may have cancelled while Minecraft was still active. No
                # reward or outbox is generated; the client can clear recovery.
                return self.snapshot()
            row = self._current()
            if row is None or row["id"] != key or row["player"] != player or row["instance"] != instance:
                raise Conflict("result does not belong to this session owner")
            if row["status"] == "RETURN_PENDING" and row["outcome"] == outcome:
                self._write_outbox(row, outcome)
                return self.snapshot()
            if row["status"] != "ACTIVE":
                raise Conflict("session is not active")
            request = Request(**json.loads(row["request"]))
            scenario = self.scenarios[request.scenario]
            if outcome not in {scenario["won"],scenario["lost"],scenario["aborted"]}:
                raise Conflict("outcome not permitted for this scenario")
            self.db.execute("UPDATE sessions SET status='RETURN_PENDING',outcome=?,updated=? WHERE id=?", (outcome,time.time(),key))
            self.db.commit()
            self._write_outbox(row, outcome)
            return self.snapshot()

    def _write_outbox(self, row, outcome):
        request = Request(**json.loads(row["request"]))
        data = {"session":row["id"],"command":command(request,self.outcomes[outcome]),"acknowledged":False}
        tmp = self.directory / "return-command.json.tmp"
        tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
        tmp.replace(self.directory / "return-command.json")

    def acknowledge(self, ack: Ack) -> bool:
        with self.lock:
            row = self._current()
            if row is None:
                return False
            request = Request(**json.loads(row["request"]))
            if (request.character,request.sequence) != (ack.character,ack.sequence):
                return False
            if ack.outcome != 'aborted' and (row['status'] != 'RETURN_PENDING' or row['outcome'] != ack.outcome):
                return False
            self.db.execute("UPDATE sessions SET status='COMPLETE',outcome=?,updated=? WHERE id=?", (ack.outcome,time.time(),row["id"]))
            self.db.commit()
            outbox = self.directory / "return-command.json"
            if outbox.exists():
                outbox.unlink()
            return True
