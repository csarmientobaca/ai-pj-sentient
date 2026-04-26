from django.conf import settings
from openai import OpenAI

from django.http import HttpResponse
from .models import Character
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

    return JsonResponse({
        "character": character.name,
        "mood": character.mood,
        "message": message,
        "memories_used": [memory.content for memory in memories],
        "response": ai_response.output_text,
    })