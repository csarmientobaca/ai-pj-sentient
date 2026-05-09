from django.urls import path
from .views import (
    register,
    character_list,
    create_character,
    talk_to_character,
    run_REM_phase_sleep,
    set_api_key,
)

urlpatterns = [
    path("auth/register/", register, name="register"),
    path("auth/api-key/", set_api_key, name="set_api_key"),
    path("characters/", character_list, name="character_list"),
    path("characters/create/", create_character, name="create_character"),
    path("characters/<int:character_id>/talk/", talk_to_character, name="talk_to_character"),
    path("characters/<int:character_id>/rem-sleep/", run_REM_phase_sleep, name="run_REM_phase_sleep"),
]
