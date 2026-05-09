from datetime import date
from core.models import Memory
from core.services import ai


def run_REM_phase_sleep(character, api_key=None):
    """
    Consolidates today's daily memories into a REM_PHASE summary.
    Returns a result dict with status and summary info.
    """
    today_memories = character.memories.filter(
        memory_type=Memory.MemoryType.DAILY,
        created_at__date=date.today(),
    )

    if not today_memories.exists():
        return {"status": "no memories today"}

    existing_rem = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE,
        created_at__date=date.today(),
    ).first()

    if existing_rem:
        return {
            "status": "REM already done today",
            "summary": existing_rem.content,
        }

    daily_memory_text = "\n".join(m.content for m in today_memories)
    rem_result = ai._REM_phase_sleep(character, daily_memory_text, api_key=api_key)
    summary = rem_result["summary"]

    Memory.objects.create(
        character=character,
        content=summary,
        importance=9,
        memory_type=Memory.MemoryType.REM_PHASE,
    )
    today_memories.update(is_consolidated=True)

    return {
        "status": "REM complete",
        "summary": summary,
        "important_points": rem_result["important_points"],
    }
