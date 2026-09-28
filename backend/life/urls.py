from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views as v
r = DefaultRouter()
for name, vs in [("activities", v.ActivityViewSet), ("todos", v.TodoViewSet), ("habits", v.HabitViewSet),
                 ("habit-logs", v.HabitLogViewSet), ("memories", v.MemoryViewSet)]: r.register(name, vs, basename=name)
urlpatterns = [path("today/", v.today), path("habits-today/", v.habits_today)] + r.urls
