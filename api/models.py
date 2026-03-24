from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255, default="Sans titre", blank=True)
    content = models.TextField(default="", blank=True)
    word_count = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Aide les analyseurs de types (Pylance/Pyright) à reconnaître le manager Django.
    objects = models.Manager()

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        self.word_count = len(str(self.content).split())
        return super().save(*args, **kwargs)
