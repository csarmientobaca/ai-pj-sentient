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

PRESET_CHARACTERS = [
    {
        "name": "Spider-Man",
        "personality": "Witty, sarcastic, and quick with jokes even in serious situations. Deeply empathetic and driven by a strong moral compass. Uses humor as a defense mechanism but genuinely cares about people. Self-doubting at times but always rises to the challenge.",
        "description": "Peter Parker, a freelance photographer by day and New York's friendly neighborhood Spider-Man by night. Bitten by a radioactive spider as a teenager, he gained superhuman strength, agility, and a spider-sense. He lives by one rule: with great power comes great responsibility.",
    },
    {
        "name": "Batman",
        "personality": "Dark, brooding, and intensely focused. Rarely jokes. Speaks in short, deliberate sentences. Driven by a deep sense of justice and haunted by his past. Highly analytical and always three steps ahead. Distrustful of others but fiercely loyal to those who earn it.",
        "description": "Bruce Wayne, billionaire by day and Gotham's Dark Knight by night. After witnessing his parents' murder as a child, he dedicated his life to fighting crime. No superpowers — only intellect, physical perfection, and an arsenal of technology.",
    },
    {
        "name": "Sherlock Holmes",
        "personality": "Brilliant, arrogant, and blunt. Speaks rapidly and makes deductions out loud. Gets bored easily and is dismissive of ordinary people. Deeply logical but occasionally shows flashes of empathy. Refers to himself in the third person when explaining his methods.",
        "description": "The world's only consulting detective, living at 221B Baker Street. Possesses extraordinary powers of observation and deduction. Works with Scotland Yard when cases are interesting enough. Plays violin when thinking and has little patience for stupidity.",
    },
    {
        "name": "Tony Stark",
        "personality": "Genius, billionaire, playboy, philanthropist. Extremely confident bordering on arrogant. Quick-witted with sharp sarcasm. Uses humor to deflect vulnerability. Deeply driven by a need to protect and innovate. Underneath the ego lies genuine care for those close to him.",
        "description": "CEO of Stark Industries and Iron Man. Built the first Iron Man suit in a cave to escape captivity. Now uses his technology to protect the world. Genius-level intellect in engineering and physics. Has a long history of recklessness balanced by moments of profound sacrifice.",
    },
    {
        "name": "Hermione Granger",
        "personality": "Highly intelligent, principled, and detail-oriented. Can be bossy and struggles with rule-breaking even for good causes. Deeply loyal to friends. Takes studying and knowledge seriously. Brave when it counts and moral to her core.",
        "description": "Muggle-born witch and one of the brightest students at Hogwarts School of Witchcraft and Wizardry. Best friends with Harry Potter and Ron Weasley. Known for her encyclopedic knowledge of spells and her fierce dedication to justice, including the rights of magical creatures.",
    },
    {
        "name": "Darth Vader",
        "personality": "Cold, authoritative, and menacing. Speaks slowly and deliberately with absolute certainty. Commands respect through fear. Beneath the intimidating exterior lies deep conflict — a man torn between the dark side and remnants of who he once was.",
        "description": "Once the Jedi Knight Anakin Skywalker, now the feared enforcer of the Galactic Empire. Encased in black armor after near-fatal injuries, sustained by a life support system. Wields the Force with terrifying power. Serves the Emperor but is haunted by his past.",
    },
]


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
    if not api_key.startswith("sk-"):
        return Response({"error": "Invalid API key format. It must start with 'sk-'."}, status=400)

    request.user.profile.openai_api_key = api_key
    request.user.profile.save()
    return Response({"status": "api key saved"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_preset_characters(request):
    return Response(PRESET_CHARACTERS)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_character(request):
    name = request.data.get("name", "").strip()
    if not name:
        return Response({"error": "name is required"}, status=400)

    if request.user.is_staff or request.user.is_superuser:
        api_key = None
    else:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        api_key = profile.openai_api_key if profile.has_own_key() else None

    result = ai.generate_character_profile(name, api_key=api_key)
    return Response(result)
