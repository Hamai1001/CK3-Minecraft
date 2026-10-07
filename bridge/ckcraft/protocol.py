"""Strict versioned log frames emitted by the CK3 mod."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib


def integer(value: str, low: int, high: int) -> int:
    try:
        number = Decimal(value)
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError("non-integral number")
        result = int(number)
    except (InvalidOperation, OverflowError) as error:
        raise ValueError("invalid numeric game field") from error
    if not low <= result <= high:
        raise ValueError("game field outside protocol limits")
    return result


@dataclass(frozen=True)
class Request:
    scenario: str
    character: int
    sequence: int
    prowess: int
    opponent: int
    opponent_prowess: int
    province: int
    name: str
    opponent_name: str

    def identity(self, campaign: str) -> str:
        return hashlib.sha256(f"{campaign}:{self.character}:{self.sequence}".encode()).hexdigest()[:32]


@dataclass(frozen=True)
class Ack:
    character: int
    sequence: int
    outcome: str


def parse_line(line: str) -> Request | Ack | None:
    start = line.find("CKCRAFT1|")
    if start < 0:
        return None
    parts = line[start:].rstrip("\r\n").split("|")
    if len(parts) == 5 and parts[1] == "ACK":
        if parts[4] not in {"won", "lost", "aborted", "travelled"}:
            raise ValueError("unknown acknowledgement outcome")
        return Ack(integer(parts[2], 1, 2**32-1), integer(parts[3], 1, 2**31-1), parts[4])
    if len(parts) != 11 or parts[1] != "REQUEST":
        raise ValueError("invalid CKCRAFT1 frame")
    if parts[2] not in {"travel_duel", "free_travel"}:
        raise ValueError("unknown scenario")
    if any(not s or len(s) > 160 or any(ord(c) < 32 for c in s) for s in parts[9:]):
        raise ValueError("invalid character name")
    request = Request(parts[2], integer(parts[3], 1, 2**32-1), integer(parts[4], 1, 2**31-1),
                      integer(parts[5], 0, 1000), integer(parts[6], 0, 2**32-1),
                      integer(parts[7], 0, 1000), integer(parts[8], 1, 2**31-1), parts[9], parts[10])
    if request.scenario == "travel_duel" and (not request.opponent or request.character == request.opponent):
        raise ValueError("duel requires a distinct real CK3 opponent")
    return request
