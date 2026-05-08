from django.http import HttpResponse, JsonResponse
from .models import Character, Interaction
from .services import ai, memory, sleep


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

    memory_decision, memory_created, memory_already_exists = memory.process_memory_decision(character, message)

    context_memories = memory.get_context_memories(character)
    memory_text = "\n".join(m.content for m in context_memories)

    response_text = ai.generate_response(character, message, memory_text)

    Interaction.objects.create(
        character=character,
        message=message,
        response=response_text,
    )

    return JsonResponse({
        "character": character.name,
        "memory_created": memory_created.content if memory_created else None,
        "memory_already_exists": memory_already_exists,
        "mood": character.mood,
        "message": message,
        "memories_used": [m.content for m in context_memories],
        "response": response_text,
        "memory_decision": memory_decision,
    })


def run_REM_phase_sleep(request, character_id):
    character = Character.objects.get(id=character_id)
    result = sleep.run_REM_phase_sleep(character)
    return JsonResponse(result)
