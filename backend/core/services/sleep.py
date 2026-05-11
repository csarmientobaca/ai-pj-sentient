from datetime import date
from core.models import Memory
from core.services import ai


def run_REM_phase_sleep(character, api_key=None):
    """
    Consolidates today's daily memories into a single REM_PHASE summary.
    If a previous REM summary exists, merges with it instead of appending.
    """
    today_memories = character.memories.filter(
        memory_type=Memory.MemoryType.DAILY,
        created_at__date=date.today(),
    )

    if not today_memories.exists():
        return {"status": "no memories today"}

    existing_rem_today = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE,
        created_at__date=date.today(),
    ).first()

    if existing_rem_today:
        return {
            "status": "REM already done today",
            "summary": existing_rem_today.content,
        }

    daily_memory_text = "\n".join(m.content for m in today_memories)

    all_rem_memories = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE,
    ).order_by("created_at")

    if all_rem_memories.exists():
        existing_summary = "\n".join(m.content for m in all_rem_memories)
        rem_result = ai.merge_REM_memories(
            character, existing_summary, daily_memory_text, api_key=api_key
        )
        all_rem_memories.delete()
    else:
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
