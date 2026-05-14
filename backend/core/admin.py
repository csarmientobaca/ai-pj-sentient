from django.contrib import admin
from .models import Character, Memory, Interaction, Profile

admin.site.register(Character)
admin.site.register(Memory)
admin.site.register(Interaction)
admin.site.register(Profile)