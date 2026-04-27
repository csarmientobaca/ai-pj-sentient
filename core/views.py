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
        existing_memories = character.memories.order_by("-importance", "-created_at")[:10]
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
        created_at__date=date.today()
    ).order_by("-importance", "-created_at")[:5]

    consolidated_memories = character.memories.filter(
        memory_type=Memory.MemoryType.CONSOLIDATED
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

    summary = _REM_phase_sleep(character, daily_memory_text)

    Memory.objects.create(
        character=character,
        content=summary,
        importance=9,
        memory_type=Memory.MemoryType.AFTER_REM_PHASE,
    )

    return JsonResponse({
        "status": "sleep complete",
        "summary": summary
    })



def _REM_phase_sleep(character, daily_memory_text):
    result = client.responses.create(
        model="gpt-4.1-mini",
        instructions=f"""
        You are consolidating memories for {character.name}, like a sleep process.

        Character personality:
        {character.personality}

        Task:
        - Read today's memories only.
        - Create one concise long-term memory summary.
        - Remove duplicates.
        - Keep only important facts, relationships, goals, emotional events, or repeated patterns.
        - Do not include random small talk.
        - Write in third person.
        - Keep it short.
        """,
        input=daily_memory_text,
    )

    return result.output_text
