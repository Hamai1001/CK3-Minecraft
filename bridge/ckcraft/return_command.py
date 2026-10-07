"""Commands only contain validated numbers and table-selected event IDs."""
from .protocol import Request


def command(request: Request, outcome: dict) -> str:
    # CK3's own guard prevents a late result targeting the next event. Applying a
    # result removes the pending flag; repeating this command cannot grant twice.
    return (f"effect character:{request.character} = {{ if = {{ limit = {{ "
            f"has_character_flag = ckcraft_pending var:ckcraft_sequence = {request.sequence} "
            f"}} trigger_event = {{ id = {outcome['ck3_event']} }} }} }}")
