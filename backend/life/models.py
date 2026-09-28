import os, uuid
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from django.utils import timezone
U = settings.AUTH_USER_MODEL
class Activity(models.Model):
    user = models.ForeignKey(U, on_delete=models.CASCADE); name = models.CharField(max_length=80)
    minutes = models.PositiveIntegerField(); notes = models.CharField(max_length=200, blank=True)
    date = models.DateField(default=timezone.localdate); created_at = models.DateTimeField(auto_now_add=True)
class Todo(models.Model):
    REASONS = [("forgot", "Forgot"), ("no_time", "No time"), ("busy", "Busy"), ("unwell", "Not feeling well"), ("other", "Other")]
    user = models.ForeignKey(U, on_delete=models.CASCADE); title = models.CharField(max_length=200)
    plan_date = models.DateField(default=timezone.localdate)   # set to tomorrow when planning at night
    done = models.BooleanField(default=False); skip_reason = models.CharField(max_length=20, choices=REASONS, blank=True); skip_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
class Habit(models.Model):
    FREQ = [("daily", "Every day"), ("weekly", "Specific weekdays"), ("interval", "Every N hours")]
    user = models.ForeignKey(U, on_delete=models.CASCADE); name = models.CharField(max_length=80)
    frequency = models.CharField(max_length=10, choices=FREQ, default="daily")
    weekdays = models.CharField(max_length=20, blank=True, help_text="0=Mon..6=Sun, comma separated")
    interval_hours = models.PositiveIntegerField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True); end_time = models.TimeField(null=True, blank=True)
    start_date = models.DateField(default=timezone.localdate); end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField(default=timezone.localdate); done = models.BooleanField(default=True)
    reason = models.CharField(max_length=120, blank=True); slot = models.CharField(max_length=5, blank=True)  # "08:00" for interval habits
    class Meta: unique_together = ("habit", "date", "slot")
    class Meta: unique_together = ("habit", "date")
class Memory(models.Model):
    user = models.ForeignKey(U, on_delete=models.CASCADE); text = models.TextField()
    category = models.CharField(max_length=40, default="Other")
    created_at = models.DateTimeField(auto_now_add=True)   # date + time recorded automatically


def _upload_path(inst, name):  # unguessable name, grouped per user
    return f"memories/u{inst.memory.user_id}/{uuid.uuid4().hex}{os.path.splitext(name)[1].lower()}"
class MemoryAttachment(models.Model):
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=_upload_path)   # stored in Oracle Object Storage, or media/ when no bucket is configured
    name = models.CharField(max_length=200); size = models.PositiveIntegerField(); content_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
@receiver(post_delete, sender=MemoryAttachment)
def _remove_file(sender, instance, **kw): instance.file.delete(save=False)
