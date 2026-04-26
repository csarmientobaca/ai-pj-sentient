from django.conf import settings
from openai import OpenAI

from django.http import HttpResponse
from .models import Character, Interaction, Memory
from django.http import JsonResponse


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
                importance=5,
            )

    memories = character.memories.order_by("-importance", "-created_at")[:3]

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
    })