from datetime import time
from rest_framework import serializers, viewsets, decorators
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
import os
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import *
def make(model, order):
    class S(serializers.ModelSerializer):
        class Meta: model = None; fields = "__all__"; read_only_fields = ["user"]
    S.Meta.model = model
    class V(viewsets.ModelViewSet):
        serializer_class = S
        def get_queryset(self):
            q = model.objects.filter(user=self.request.user) if hasattr(model, "user") else model.objects.filter(habit__user=self.request.user)
            return q.order_by(*order)
        def _own(self, s):  # a habit log may only point at the caller's own habit
            h = s.validated_data.get("habit")
            if h is not None and h.user_id != self.request.user.id: raise PermissionDenied()
        def perform_create(self, s):
            self._own(s); s.save(user=self.request.user) if hasattr(model, "user") else s.save()
        def perform_update(self, s):
            self._own(s); s.save()
    return V
ActivityViewSet = make(Activity, ["-date", "-created_at"]); TodoViewSet = make(Todo, ["-plan_date", "id"])
HabitViewSet = make(Habit, ["name"]); HabitLogViewSet = make(HabitLog, ["-date"])
def slots(h, d):
    """Times a habit is due on day d: [""] for once-a-day habits, ["06:00", "09:00", ...] for every-N-hours habits."""
    if d < h.start_date or (h.end_date and d > h.end_date): return []
    if h.frequency == "weekly" and str(d.weekday()) not in h.weekdays.split(","): return []
    if h.frequency != "interval" or not h.interval_hours: return [""]
    st = h.start_time or time(6, 0); cur = st.hour * 60 + st.minute
    cut = h.end_time.hour * 60 + h.end_time.minute if h.end_time and h.end_date and d == h.end_date else 1439
    out = []
    while cur <= cut: out.append(f"{cur // 60:02d}:{cur % 60:02d}"); cur += h.interval_hours * 60
    return out
def habit_rows(u, d):
    logs = {(l.habit_id, l.slot): l for l in HabitLog.objects.filter(habit__user=u, date=d)}; rows = []
    for h in Habit.objects.filter(user=u):
        for s in slots(h, d):
            l = logs.get((h.id, s)); rows.append({"habit": h.id, "name": h.name, "slot": s, "done": None if l is None else l.done, "reason": l.reason if l else ""})
    return sorted(rows, key=lambda r: (r["slot"], r["name"]))
@decorators.api_view(["GET", "POST"])
def habits_today(request):
    u, d = request.user, timezone.localdate()
    if request.method == "POST":
        h = Habit.objects.filter(user=u, id=request.data.get("habit")).first(); slot = request.data.get("slot", "")
        if not h or slot not in slots(h, d): return Response({"detail": "This habit is not scheduled for that time today."}, 400)
        HabitLog.objects.update_or_create(habit=h, date=d, slot=slot, defaults={"done": bool(request.data.get("done")), "reason": str(request.data.get("reason", ""))[:120]})
    return Response(habit_rows(u, d))
@decorators.api_view(["GET"])
def today(request):
    u, d = request.user, timezone.localdate(); todos = Todo.objects.filter(user=u, plan_date=d)
    rows = habit_rows(u, d); done = sum(1 for r in rows if r["done"]); by = {}
    for a in Activity.objects.filter(user=u, date=d): by[a.name] = by.get(a.name, 0) + a.minutes
    return Response({"todos_done": todos.filter(done=True).count(), "todos_total": todos.count(),
        "activities": [{"name": n, "minutes": m} for n, m in sorted(by.items(), key=lambda x: -x[1])],
        "habits_done": done, "habits_total": len(rows), "habits_pct": round(100 * done / len(rows)) if rows else 0,
        "memories": Memory.objects.filter(user=u).count()})

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}; IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_MB, MAX_FILES = 10, 5
class MemorySerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    class Meta: model = Memory; fields = ["id", "text", "category", "created_at", "attachments"]; read_only_fields = ["created_at"]
    def get_attachments(self, m):
        req = self.context.get("request")
        def url(a): u = a.file.url; return req.build_absolute_uri(u) if req and u.startswith("/") else u
        return [{"id": a.id, "name": a.name, "size": a.size, "url": url(a), "image": os.path.splitext(a.name)[1].lower() in IMAGES} for a in m.attachments.all()]
    def validate_category(self, v):
        v = " ".join(v.split())[:40]   # any custom category is allowed
        if not v: raise serializers.ValidationError("Choose or type a category.")
        return v
class MemoryViewSet(make(Memory, ["-created_at"])):
    serializer_class = MemorySerializer
    def get_queryset(self): return super().get_queryset().prefetch_related("attachments")
    @decorators.action(detail=True, methods=["post"], url_path="attachments")
    def add_attachment(self, request, pk=None):
        m = self.get_object(); f = request.FILES.get("file")
        if not f: return Response({"detail": "Choose a file."}, 400)
        if os.path.splitext(f.name)[1].lower() not in ALLOWED: return Response({"detail": "This file type is not allowed. Use an image, PDF, Word, Excel or text file."}, 400)
        if f.size > MAX_MB * 1024 * 1024: return Response({"detail": f"Files must be under {MAX_MB} MB."}, 400)
        if m.attachments.count() >= MAX_FILES: return Response({"detail": f"A memory can have up to {MAX_FILES} attachments."}, 400)
        MemoryAttachment.objects.create(memory=m, file=f, name=f.name[:200], size=f.size, content_type=f.content_type or "")
        return Response(MemorySerializer(self.get_queryset().get(pk=m.pk), context={"request": request}).data, 201)  # re-read so the new file shows
    @decorators.action(detail=True, methods=["delete"], url_path=r"attachments/(?P<att>\d+)")
    def remove_attachment(self, request, pk=None, att=None):
        get_object_or_404(MemoryAttachment, id=att, memory=self.get_object()).delete(); return Response(status=204)
