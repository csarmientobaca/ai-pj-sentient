from django.db import models


class Character(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    mood = models.CharField(max_length=50, default="neutral")

    def __str__(self):
        return self.name


class Memory(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="memories")
    content = models.TextField()
    importance = models.IntegerField(default=1)
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