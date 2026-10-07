"""Commands only contain validated numbers and table-selected event IDs."""
from .protocol import Request


def command(request: Request, outcome: dict) -> str:
    # GetID yields a runtime ID; character:<key> resolves historical script keys.
    # Use the actual character reference stored by the request event instead.
    # The global sequence is unique across player characters in this campaign.
    # Applying a result clears the actor reference and flag, so replay is inert.
    return ("effect if = { limit = { exists = global_var:ckcraft_return_actor } "
            "global_var:ckcraft_return_actor = { if = { limit = { "
            f"has_character_flag = ckcraft_pending var:ckcraft_sequence = {request.sequence} "
            f"}} trigger_event = {{ id = {outcome['ck3_event']} }} }} }} }}")
