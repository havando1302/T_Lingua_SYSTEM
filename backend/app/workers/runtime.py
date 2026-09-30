"""Small lifecycle helpers shared by the three streaming stages."""
from app.core.telemetry import GLOBAL_TELEMETRY


def release_work(item: dict) -> None:
    session = item.get("session")
    if session is not None and item.get("work_reserved"):
        item["work_reserved"] = False
        session.pending_utterances = max(0, getattr(session, "pending_utterances", 0) - 1)
        turn = item.get("turn")
        pending = getattr(session, "pending_by_turn", {})
        if turn:
            remaining = max(0, pending.get(turn.turn_id, 0) - 1)
            if remaining:
                pending[turn.turn_id] = remaining
            else:
                pending.pop(turn.turn_id, None)


async def complete_if_idle(session, turn) -> None:
    if not session or not turn or not session.is_running:
        return
    current = getattr(session, "active_turns", {}).get(turn.turn_id)
    if current is None or current.status != "processing" or getattr(session, "pending_by_turn", {}).get(turn.turn_id, 0):
        return
    from app.models.turn_model import TurnStatus
    completed = current.with_status(TurnStatus.COMPLETED)
    session.active_turns[turn.turn_id] = completed
    if session.current_turn and session.current_turn.turn_id == turn.turn_id:
        session.current_turn = completed
    await session.send_message({"type": "turn_complete", "turn_id": turn.turn_id, "status": "completed"})


async def finish_work(item: dict) -> None:
    release_work(item)
    await complete_if_idle(item.get("session"), item.get("turn"))


def discard_work(item: dict, error: str | None = None) -> None:
    GLOBAL_TELEMETRY.discard_turn(item.get("metric_id"), error=error)
    release_work(item)
