import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Character, Interaction, Profile, TRIAL_INTERACTION_LIMIT
from .services import ai, memory, sleep


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "").strip()

    if not username or not password:
        return Response({"error": "username and password are required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "username already taken"}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"status": "user created"}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def character_list(request):
    characters = Character.objects.filter(user=request.user)
    data = [
        {"id": c.id, "name": c.name, "mood": c.mood, "description": c.description}
        for c in characters
    ]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_character(request):
    name = request.data.get("name", "").strip()
    description = request.data.get("description", "").strip()
    personality = request.data.get("personality", "").strip()

    if not name:
        return Response({"error": "name is required"}, status=400)

    character = Character.objects.create(
        user=request.user,
        name=name,
        description=description,
        personality=personality,
    )
    return Response({"id": character.id, "name": character.name}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def talk_to_character(request, character_id):
    try:
        character = Character.objects.get(id=character_id, user=request.user)
    except Character.DoesNotExist:
        return Response({"error": "character not found"}, status=404)

    message = request.data.get("message", "")
    profile = None
    if request.user.is_staff or request.user.is_superuser:
        api_key = None
    else:
        profile = request.user.profile
        if profile.has_own_key():
            api_key = profile.openai_api_key
        elif profile.trial_remaining() > 0:
            api_key = None
        else:
            return Response(
                {"error": f"Trial limit of {TRIAL_INTERACTION_LIMIT} interactions reached. Add your OpenAI API key to continue."},
                status=402,
            )

    memory_decision, memory_created, memory_already_exists = memory.process_memory_decision(character, message, api_key=api_key)

    context_memories = memory.get_context_memories(character)
    memory_text = "\n".join(m.content for m in context_memories)

    response_text = ai.generate_response(character, message, memory_text, api_key=api_key)

    if profile and not profile.has_own_key():
        profile.trial_interactions_used += 1
        profile.save()

    Interaction.objects.create(
        character=character,
        message=message,
        response=response_text,
    )

    return Response({
        "character": character.name,
        "memory_created": memory_created.content if memory_created else None,
        "memory_already_exists": memory_already_exists,
        "mood": character.mood,
        "message": message,
        "memories_used": [m.content for m in context_memories],
        "response": response_text,
        "memory_decision": memory_decision,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_REM_phase_sleep(request, character_id):
    try:
        character = Character.objects.get(id=character_id, user=request.user)
    except Character.DoesNotExist:
        return Response({"error": "character not found"}, status=404)

    if request.user.is_staff or request.user.is_superuser:
        api_key = None
    else:
        profile = request.user.profile
        api_key = profile.openai_api_key if profile.has_own_key() else None
    result = sleep.run_REM_phase_sleep(character, api_key=api_key)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return Response({
        "username": request.user.username,
        "has_own_key": profile.has_own_key(),
        "trial_interactions_used": profile.trial_interactions_used,
        "trial_limit": TRIAL_INTERACTION_LIMIT,
        "trial_remaining": profile.trial_remaining(),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_api_key(request):
    api_key = request.data.get("api_key", "").strip()
    if not api_key:
        return Response({"error": "api_key is required"}, status=400)

    request.user.profile.openai_api_key = api_key
    request.user.profile.save()
    return Response({"status": "api key saved"})
