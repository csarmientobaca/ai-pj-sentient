from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


TRIAL_INTERACTION_LIMIT = 5

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    openai_api_key = models.CharField(max_length=200, blank=True)
    trial_interactions_used = models.IntegerField(default=0)

    def has_own_key(self):
        return bool(self.openai_api_key)

    def trial_remaining(self):
        return max(0, TRIAL_INTERACTION_LIMIT - self.trial_interactions_used)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Character(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters", null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    mood = models.CharField(max_length=50, default="neutral")

    def __str__(self):
        return self.name


class Memory(models.Model):
    class MemoryType(models.TextChoices):
        DAILY = "daily", "Daily"
        REM_PHASE = "rem_phase", "REM Phase"


    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="memories")
    content = models.TextField()
    importance = models.IntegerField(default=1)
    memory_type = models.CharField(
        max_length=20, 
        choices=MemoryType.choices, 
        default=MemoryType.DAILY
        )


    is_consolidated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.character.name}: {self.content[:50]}"

class Interaction(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="interactions")
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.character.name}: {self.message[:50]}"