from datetime import date
from core.models import Memory
from core.services import ai


def get_existing_memories_text(character):
    memories = character.memories.exclude(
        memory_type=Memory.MemoryType.DAILY, is_consolidated=True
    ).order_by("-importance", "-created_at")[:10]
    return "\n".join(m.content for m in memories)


def get_context_memories(character):
    today_memories = character.memories.filter(
        memory_type=Memory.MemoryType.DAILY,
        created_at__date=date.today(),
        is_consolidated=False,
    ).order_by("-importance", "-created_at")[:5]

    consolidated_memories = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE
    ).order_by("-created_at")[:3]

    return list(today_memories) + list(consolidated_memories)


def process_memory_decision(character, message, api_key=None):
    """
    Decides whether to save a memory for a given message.
    Returns (memory_decision, memory_created, memory_already_exists).
    """
    if message.lower().startswith("remember that"):
        memory_content = message[len("remember that"):].strip()
        memory_decision = {
            "should_remember": True,
            "memory": memory_content,
            "importance": 5,
            "reason": "Manual remember command used.",
            "source": "manual_command",
        }
    else:
        existing_memory_text = get_existing_memories_text(character)
        memory_decision = ai.decide_memory(character, message, existing_memory_text, api_key=api_key)
        memory_content = memory_decision["memory"].strip()

    memory_created = None
    memory_already_exists = False

    if memory_decision["should_remember"]:
        memory_content = memory_decision["memory"].strip()
        duplicate = Memory.objects.filter(
            character=character,
            content__iexact=memory_content,
        ).first()

        if duplicate:
            memory_already_exists = True
        else:
            memory_created = Memory.objects.create(
                character=character,
                content=memory_content,
                importance=memory_decision["importance"],
            )

    return memory_decision, memory_created, memory_already_exists
