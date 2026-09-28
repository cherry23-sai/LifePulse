from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TxViewSet, summary, target
r = DefaultRouter(); r.register("transactions", TxViewSet, basename="tx")
urlpatterns = [path("summary/", summary), path("target/", target)] + r.urls
