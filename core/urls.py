from django.urls import path
from .views import character_list, talk_to_character

urlpatterns = [
    path("characters/", character_list, name="character_list"),
    path("characters/<int:character_id>/talk/", talk_to_character, name="talk_to_character"),
]