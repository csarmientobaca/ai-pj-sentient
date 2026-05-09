import json
from django.conf import settings
from openai import OpenAI


def _get_client(api_key: str = None) -> OpenAI:
    return OpenAI(api_key=api_key or settings.OPENAI_API_KEY)


def decide_memory(character, message, existing_memory_text, api_key=None):
    client = _get_client(api_key)
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


def generate_response(character, message, memory_text, api_key=None):
    client = _get_client(api_key)
    result = client.responses.create(
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
    return result.output_text


def _REM_phase_sleep(character, daily_memory_text, api_key=None):
    client = _get_client(api_key)
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
