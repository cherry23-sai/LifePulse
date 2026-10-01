from datetime import date, datetime
from decimal import Decimal
from rest_framework import serializers, viewsets, decorators
from rest_framework.response import Response
from django.utils import timezone
from firebase_db import now
from firestore_utils import col, doc_data
from .forecast import totals, forecast, extras

KINDS={"earning","salary","other_income","expense","saving"}
class TxSerializer(serializers.Serializer):
    id=serializers.CharField(read_only=True); user=serializers.CharField(read_only=True)
    kind=serializers.CharField(); amount=serializers.DecimalField(max_digits=12,decimal_places=2)
    category=serializers.CharField(required=False,allow_blank=True); note=serializers.CharField(required=False,allow_blank=True)
    why=serializers.CharField(required=False,allow_blank=True); place=serializers.CharField(required=False,allow_blank=True)
    date=serializers.DateField(required=False); created_at=serializers.CharField(read_only=True)
    def validate_kind(self,v):
        if v not in KINDS: raise serializers.ValidationError("Invalid transaction type.")
        return v
    def validate(self,a):
        if a.get("kind")=="expense" and not (a.get("why") and a.get("place")):
            raise serializers.ValidationError("Tell us why and where you spent it.")
        return a

def _all(user):
    docs=list(col(user,"transactions").stream())
    def key(x):
        d=x.to_dict(); return (str(d.get("date","")),str(d.get("created_at","")))
    return sorted(docs,key=key,reverse=True)

class TxViewSet(viewsets.ViewSet):
    def list(self,request):
        k=request.query_params.get("kind"); out=[]
        for d in _all(request.user):
            x=doc_data(d)
            if not k or x.get("kind")==k: out.append(x)
        return Response(out)
    def create(self,request):
        s=TxSerializer(data=request.data); s.is_valid(raise_exception=True); a=s.validated_data
        ref=col(request.user,"transactions").document()
        data=dict(a); data["amount"]=float(data["amount"]); data["date"]=data.get("date",timezone.localdate()).isoformat()
        data["created_at"]=datetime.now().isoformat(); data["user"]=str(request.user.id)
        ref.set(data); data["id"]=ref.id
        return Response(data,201)
    def retrieve(self,request,pk=None):
        d=col(request.user,"transactions").document(pk).get()
        if not d.exists:return Response({"detail":"Not found."},404)
        return Response(doc_data(d))
    def update(self,request,pk=None):
        ref=col(request.user,"transactions").document(pk); old=ref.get()
        if not old.exists:return Response({"detail":"Not found."},404)
        s=TxSerializer(data=request.data); s.is_valid(raise_exception=True); a=s.validated_data
        data=dict(a); data["amount"]=float(data["amount"]); data["date"]=data.get("date",timezone.localdate()).isoformat()
        ref.update(data); return Response(doc_data(ref.get()))
    def partial_update(self,request,pk=None):
        ref=col(request.user,"transactions").document(pk); old=ref.get()
        if not old.exists:return Response({"detail":"Not found."},404)
        merged=old.to_dict(); merged.update(request.data); merged.pop("id",None)
        s=TxSerializer(data=merged); s.is_valid(raise_exception=True); a=s.validated_data
        data=dict(a); data["amount"]=float(data["amount"]); data["date"]=data.get("date",old.to_dict().get("date",timezone.localdate().isoformat()))
        ref.update(data); return Response(doc_data(ref.get()))
    def destroy(self,request,pk=None):
        ref=col(request.user,"transactions").document(pk)
        if not ref.get().exists:return Response(status=404)
        ref.delete(); return Response(status=204)

@decorators.api_view(["GET","PUT"])
def target(request):
    first=timezone.localdate().replace(day=1).isoformat(); ref=col(request.user,"targets").document(first)
    if request.method=="PUT":
        amount=float(request.data.get("amount",0)); ref.set({"month":first,"amount":amount},merge=True)
    d=ref.get(); return Response({"amount":float((d.to_dict() or {}).get("amount",0)) if d.exists else 0})

@decorators.api_view(["GET"])
def summary(request):
    return Response({**totals(request.user),**extras(request.user),"forecast":forecast(request.user)})
