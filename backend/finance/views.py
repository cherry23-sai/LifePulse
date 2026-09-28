from datetime import date
from rest_framework import serializers, viewsets, decorators
from rest_framework.response import Response
from django.utils import timezone
from .models import Transaction, MonthlyTarget
from .forecast import totals, forecast, extras
class TxSerializer(serializers.ModelSerializer):
    class Meta: model = Transaction; fields = "__all__"; read_only_fields = ["user", "created_at"]
    def validate(self, a):
        if a.get("kind") == "expense" and not (a.get("why") and a.get("place")):
            raise serializers.ValidationError("Tell us why and where you spent it.")
        return a
class TxViewSet(viewsets.ModelViewSet):
    serializer_class = TxSerializer
    def get_queryset(self):
        q = Transaction.objects.filter(user=self.request.user).order_by("-date", "-created_at")
        k = self.request.query_params.get("kind"); return q.filter(kind=k) if k else q
    def perform_create(self, s): s.save(user=self.request.user)
class TargetSerializer(serializers.ModelSerializer):
    class Meta: model = MonthlyTarget; fields = ["month", "amount"]
@decorators.api_view(["GET", "PUT"])
def target(request):
    first = timezone.localdate().replace(day=1)
    if request.method == "PUT":
        MonthlyTarget.objects.update_or_create(user=request.user, month=first, defaults={"amount": request.data["amount"]})
    t = MonthlyTarget.objects.filter(user=request.user, month=first).first()
    return Response({"amount": float(t.amount) if t else 0})
@decorators.api_view(["GET"])
def summary(request): return Response({**totals(request.user), **extras(request.user), "forecast": forecast(request.user)})
