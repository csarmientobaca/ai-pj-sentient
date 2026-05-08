import json
from django.conf import settings
from datetime import date
from openai import OpenAI

from django.http import HttpResponse, JsonResponse
from .models import Character, Interaction, Memory


client = OpenAI(api_key=settings.OPENAI_API_KEY)

def character_list(request):
    characters = Character.objects.all()

    html = "<h1>Characters</h1>"

    for character in characters:
        html += f"""
        <h2>{character.name}</h2>
        <p><strong>Mood:</strong> {character.mood}</p>
        <p>{character.description}</p>
        <p><strong>Personality:</strong> {character.personality}</p>
        <hr>
        """

    return HttpResponse(html)

def talk_to_character(request, character_id):
    message = request.GET.get("message", "")

    character = Character.objects.get(id=character_id)

    memory_created = None
    memory_already_exists = False

    if message.lower().startswith("remember that"):
        memory_content = message[len("remember that"):].strip()
        memory_importance = 5

        memory_decision = {
            "should_remember": True,
            "memory": memory_content,
            "importance": memory_importance,
            "reason": "Manual remember command used.",
            "source": "manual_command",
        }
    else:
        existing_memories = character.memories.exclude(
            memory_type=Memory.MemoryType.DAILY, is_consolidated=True
        ).order_by("-importance", "-created_at")[:10]
        existing_memory_text = "\n".join(memory.content for memory in existing_memories)
        
        memory_decision = decide_memory(character, message, existing_memory_text)
        memory_content = memory_decision["memory"].strip()
        memory_importance = memory_decision["importance"]

    if memory_decision["should_remember"]:
        existing_memory = Memory.objects.filter(
            character=character,
            content__iexact=memory_content,
        ).first()

        if existing_memory:
            memory_already_exists = True
        else:
            memory_created = Memory.objects.create(
                character=character,
                content=memory_content,
                importance=memory_importance,
            )

    today_memories = character.memories.filter(
        memory_type=Memory.MemoryType.DAILY,
        created_at__date=date.today(),
        is_consolidated=False,
    ).order_by("-importance", "-created_at")[:5]

    consolidated_memories = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE
    ).order_by("-created_at")[:3]

    memories = list(today_memories) + list(consolidated_memories)
    memory_text = "\n".join(memory.content for memory in memories)

    ai_response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=f"""
        You are roleplaying as {character.name}.

        Personality:
        {character.personality}

        Current mood:
        {character.mood}

        Relevant memories:
        {memory_text}

        Stay in character. Reply naturally and briefly.
        """,
            input=message,
    )
    Interaction.objects.create(
        character=character,
        message=message,
        response=ai_response.output_text,
        )

    return JsonResponse({
        "character": character.name,
        "memory_created": memory_created.content if memory_created else None,
        "memory_already_exists": memory_already_exists,
        "mood": character.mood,
        "message": message,
        "memories_used": [memory.content for memory in memories],
        "response": ai_response.output_text,
        "memory_decision": memory_decision,
    })

def decide_memory(character, message, existing_memory_text):
    result = client.responses.create(
        model="gpt-4.1-mini",
        instructions=f"""
    You decide if a user message should become a long-term memory for {character.name}.

    Existing memories:
    {existing_memory_text}

    Rules:
    - Save stable/useful facts, preferences, relationships, goals, or important events.
    - Do NOT save greetings, jokes, random small talk, or temporary information.
    - Do NOT save information already present in existing memories.
    - If the message says the same thing in different words, do not save it again.
    - If it adds a new important detail, save only the new detail.

    Return only JSON.
    """,
        input=message,
        text={
            "format": {
                "type": "json_schema",
                "name": "memory_decision",
                "schema": {
                    "type": "object",
                    "properties": {
                        "should_remember": {"type": "boolean"},
                        "memory": {"type": "string"},
                        "importance": {"type": "integer", "minimum": 1, "maximum": 10},
                        "reason": {"type": "string"},
                    },
                    "required": ["should_remember", "memory", "importance", "reason"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        },
    )

    return json.loads(result.output_text)


def run_REM_phase_sleep(request, character_id):
    character = Character.objects.get(id=character_id)

    today_memories = character.memories.filter(
        memory_type=Memory.MemoryType.DAILY,
        created_at__date=date.today()
    )

    if not today_memories.exists():
        return JsonResponse({"status": "no memories today"})

    daily_memory_text = "\n".join(m.content for m in today_memories)

    today = date.today()

    existing_rem = character.memories.filter(
        memory_type=Memory.MemoryType.REM_PHASE,
        created_at__date=today
    ).first()

    if existing_rem:
        return JsonResponse({
            "status": "REM already done today",
            "summary": existing_rem.content
        })

    rem_result = _REM_phase_sleep(character, daily_memory_text)
    summary = rem_result["summary"]

    Memory.objects.create(
        character=character,
        content=summary,
        importance=9,
        memory_type=Memory.MemoryType.REM_PHASE,
    )

    today_memories.update(is_consolidated=True)

    return JsonResponse({
        "status": "REM complete",
        "summary": summary,
        "important_points": rem_result["important_points"],
    })

"""
TODO:
still after the rem sleep and summry the day, if i talk about something that is important but the summary already got
it repeat in memory. so if in the dayly i say my name carlos. then the summary know my name and then say gain after summary
it save again.
limit the summary/token usage maybe. mke it more concise.
maybe use a different model for the summary.
maybe use a different model for the daily memories.
maybe use a different model for the rem phase.
use or 3.5 or the 5.1 mini. to more complex tasks.

play with temperature to see if it can be more concise. make it more creative. etc

"""


def _REM_phase_sleep(character, daily_memory_text):
    result = client.responses.create(
        model="gpt-4.1-mini",
        instructions=f"""
    You are consolidating memories for {character.name}, like a REM sleep process.

    Create a concise long-term memory summary.

    Rules:
    - Do NOT invent new details.
    - Preserve only facts actually stated.
    - If content is roleplay or fiction, label it as roleplay/fiction.
    - Remove duplicates.
    - Keep important facts, relationships, goals, emotional events, or repeated patterns.

    Return only JSON.
    """,
        input=daily_memory_text,   
        text={
            "format": {
                "type": "json_schema",
                "name": "rem_memory_summary",
            "schema": {
                    "type": "object",
                    "properties": {
                        "should_save": {"type": "boolean"},
                        "summary": {"type": "string"},
                        "important_points": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["should_save", "summary", "important_points"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        },
    )

    return json.loads(result.output_text)
