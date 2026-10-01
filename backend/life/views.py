from datetime import time,date,datetime
import os, uuid
from rest_framework import serializers, viewsets, decorators
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from firebase_db import col, upload_file, delete_file
from firestore_utils import doc_data

def make_serializer(fields, read_only=()):
    class S(serializers.Serializer):
        pass
    for f in fields:
        setattr(S,f,serializers.CharField(required=False,allow_blank=True))
    S.read_only_fields=set(read_only)
    return S

def parse_date(v,default=None):
    try:return date.fromisoformat(str(v)[:10])
    except:return default or timezone.localdate()

class ActivityViewSet(viewsets.ViewSet):
    def list(self,r):
        a=[doc_data(x) for x in col(r.user,"activities").stream()]
        a.sort(key=lambda x:(x.get("date",""),x.get("created_at","")),reverse=True); return Response(a)
    def create(self,r):
        d={"name":str(r.data.get("name",""))[:80],"minutes":int(r.data.get("minutes",0)),
           "notes":str(r.data.get("notes",""))[:200],"date":str(r.data.get("date") or timezone.localdate()),
           "created_at":datetime.now().isoformat()}
        ref=col(r.user,"activities").document();ref.set(d);d["id"]=ref.id;return Response(d,201)
    def retrieve(self,r,pk=None):
        d=col(r.user,"activities").document(pk).get();return Response(doc_data(d) if d.exists else {"detail":"Not found."},404 if not d.exists else 200)
    def partial_update(self,r,pk=None):
        ref=col(r.user,"activities").document(pk)
        if not ref.get().exists:return Response({"detail":"Not found."},404)
        data={k:r.data[k] for k in ("name","minutes","notes","date") if k in r.data};ref.update(data);return Response(doc_data(ref.get()))
    update=partial_update
    def destroy(self,r,pk=None):
        ref=col(r.user,"activities").document(pk)
        if not ref.get().exists:return Response(status=404)
        ref.delete();return Response(status=204)

class TodoViewSet(viewsets.ViewSet):
    def list(self,r):
        a=[doc_data(x) for x in col(r.user,"todos").stream()];a.sort(key=lambda x:(x.get("plan_date",""),x.get("created_at","")),reverse=True);return Response(a)
    def create(self,r):
        d={"title":str(r.data.get("title",""))[:200],"plan_date":str(r.data.get("plan_date") or timezone.localdate()),
           "done":bool(r.data.get("done",False)),"skip_reason":str(r.data.get("skip_reason",""))[:20],
           "skip_note":str(r.data.get("skip_note",""))[:200],"created_at":datetime.now().isoformat()}
        ref=col(r.user,"todos").document();ref.set(d);d["id"]=ref.id;return Response(d,201)
    def partial_update(self,r,pk=None):
        ref=col(r.user,"todos").document(pk)
        if not ref.get().exists:return Response({"detail":"Not found."},404)
        allowed=("title","plan_date","done","skip_reason","skip_note");ref.update({k:r.data[k] for k in allowed if k in r.data});return Response(doc_data(ref.get()))
    update=partial_update
    def retrieve(self,r,pk=None):
        d=col(r.user,"todos").document(pk);x=d.get();return Response(doc_data(x) if x.exists else {"detail":"Not found."},404 if not x.exists else 200)
    def destroy(self,r,pk=None):
        ref=col(r.user,"todos").document(pk);ref.delete();return Response(status=204)

class HabitViewSet(viewsets.ViewSet):
    def list(self,r):
        a=[doc_data(x) for x in col(r.user,"habits").stream()];a.sort(key=lambda x:x.get("name",""));return Response(a)
    def create(self,r):
        d={"name":str(r.data.get("name",""))[:80],"frequency":r.data.get("frequency","daily"),
           "weekdays":str(r.data.get("weekdays","")),"interval_hours":r.data.get("interval_hours"),
           "start_time":str(r.data.get("start_time","")),"end_time":str(r.data.get("end_time","")),
           "start_date":str(r.data.get("start_date") or timezone.localdate()),"end_date":r.data.get("end_date"),
           "created_at":datetime.now().isoformat()}
        ref=col(r.user,"habits").document();ref.set(d);d["id"]=ref.id;return Response(d,201)
    def retrieve(self,r,pk=None):
        d=col(r.user,"habits").document(pk);x=d.get();return Response(doc_data(x) if x.exists else {"detail":"Not found."},404 if not x.exists else 200)
    def partial_update(self,r,pk=None):
        ref=col(r.user,"habits").document(pk)
        if not ref.get().exists:return Response({"detail":"Not found."},404)
        ref.update({k:r.data[k] for k in ("name","frequency","weekdays","interval_hours","start_time","end_time","start_date","end_date") if k in r.data});return Response(doc_data(ref.get()))
    update=partial_update
    def destroy(self,r,pk=None): col(r.user,"habits").document(pk).delete();return Response(status=204)

class HabitLogViewSet(viewsets.ViewSet):
    def list(self,r):
        logs=[]
        for x in col(r.user,"habit_logs").stream():logs.append(doc_data(x))
        logs.sort(key=lambda x:x.get("date",""),reverse=True);return Response(logs)
    def create(self,r):
        hid=str(r.data.get("habit")); h=col(r.user,"habits").document(hid).get()
        if not h.exists:raise PermissionDenied()
        d={"habit":hid,"date":str(r.data.get("date") or timezone.localdate()),"done":bool(r.data.get("done",True)),
           "reason":str(r.data.get("reason",""))[:120],"slot":str(r.data.get("slot",""))[:5]}
        ref=col(r.user,"habit_logs").document(f"{hid}_{d['date']}_{d['slot'] or 'default'}");ref.set(d);d["id"]=ref.id;return Response(d,201)
    def destroy(self,r,pk=None):col(r.user,"habit_logs").document(pk).delete();return Response(status=204)

def habit_data(user):
    return [doc_data(x) for x in col(user,"habits").stream()]
def log_data(user):
    return [doc_data(x) for x in col(user,"habit_logs").stream()]

def slots(h,d):
    sd=parse_date(h.get("start_date"));ed=parse_date(h.get("end_date")) if h.get("end_date") else None
    if d<sd or (ed and d>ed):return []
    if h.get("frequency")=="weekly" and str(d.weekday()) not in str(h.get("weekdays","")).split(","):return []
    if h.get("frequency")!="interval" or not h.get("interval_hours"):return [""]
    st=h.get("start_time") or "06:00"; hh,mm=map(int,st[:5].split(":"));cur=hh*60+mm
    et=h.get("end_time") or "";cut=(int(et[:2])*60+int(et[3:5])) if et else 1439;out=[]
    while cur<=cut:out.append(f"{cur//60:02d}:{cur%60:02d}");cur+=int(h["interval_hours"])*60
    return out

def habit_rows(u,d):
    habits=habit_data(u); logs=log_data(u); lm={(x.get("habit"),x.get("slot","")):x for x in logs if x.get("date")==str(d)}
    rows=[]
    for h in habits:
        for s in slots(h,d):
            l=lm.get((h["id"],s));rows.append({"habit":h["id"],"name":h.get("name",""),"slot":s,"done":None if l is None else l.get("done"),"reason":l.get("reason","") if l else ""})
    return sorted(rows,key=lambda x:(x["slot"],x["name"]))

@decorators.api_view(["GET","POST"])
def habits_today(request):
    u,d=request.user,timezone.localdate()
    if request.method=="POST":
        hid=str(request.data.get("habit"));h=col(u,"habits").document(hid).get()
        if not h.exists or str(request.data.get("slot","")) not in slots(h.to_dict(),d):return Response({"detail":"This habit is not scheduled for that time today."},400)
        slot=str(request.data.get("slot",""));ref=col(u,"habit_logs").document(f"{hid}_{d}_{slot or 'default'}")
        ref.set({"habit":hid,"date":str(d),"slot":slot,"done":bool(request.data.get("done")),"reason":str(request.data.get("reason",""))[:120]})
    return Response(habit_rows(u,d))

@decorators.api_view(["GET"])
def today(request):
    u,d=request.user,timezone.localdate();todos=[doc_data(x) for x in col(u,"todos").stream() if x.to_dict().get("plan_date")==str(d)]
    rows=habit_rows(u,d);done=sum(1 for x in rows if x["done"]);by={}
    for x in col(u,"activities").stream():
        a=x.to_dict()
        if a.get("date")==str(d):by[a.get("name","")]=by.get(a.get("name",""),0)+int(a.get("minutes",0))
    memories=sum(1 for _ in col(u,"memories").stream())
    return Response({"todos_done":sum(1 for x in todos if x.get("done")),"todos_total":len(todos),
        "activities":[{"name":n,"minutes":m} for n,m in sorted(by.items(),key=lambda x:-x[1])],
        "habits_done":done,"habits_total":len(rows),"habits_pct":round(100*done/len(rows)) if rows else 0,"memories":memories})

ALLOWED={".jpg",".jpeg",".png",".webp",".gif",".pdf",".doc",".docx",".xls",".xlsx",".txt"};IMAGES={".jpg",".jpeg",".png",".webp",".gif"};MAX_MB,MAX_FILES=10,5

class MemoryViewSet(viewsets.ViewSet):
    def list(self,r):
        a=[]
        for d in col(r.user,"memories").stream():
            x=doc_data(d);atts=list(d.reference.collection("attachments").stream());x["attachments"]=[doc_data(z) for z in atts];a.append(x)
        a.sort(key=lambda x:x.get("created_at",""),reverse=True);return Response(a)
    def create(self,r):
        text=str(r.data.get("text",""));category=" ".join(str(r.data.get("category","Other")).split())[:40] or "Other"
        ref=col(r.user,"memories").document();d={"text":text,"category":category,"created_at":datetime.now().isoformat()};ref.set(d);d["id"]=ref.id;d["attachments"]=[];return Response(d,201)
    def retrieve(self,r,pk=None):
        ref=col(r.user,"memories").document(pk);d=ref.get()
        if not d.exists:return Response({"detail":"Not found."},404)
        x=doc_data(d);x["attachments"]=[doc_data(z) for z in ref.collection("attachments").stream()];return Response(x)
    def partial_update(self,r,pk=None):
        ref=col(r.user,"memories").document(pk)
        if not ref.get().exists:return Response({"detail":"Not found."},404)
        ref.update({"text":str(r.data.get("text","")),"category":" ".join(str(r.data.get("category","Other")).split())[:40]});return self.retrieve(r,pk)
    update=partial_update
    def destroy(self,r,pk=None):
        ref=col(r.user,"memories").document(pk)
        if not ref.get().exists:return Response(status=404)
        for a in ref.collection("attachments").stream():
            delete_file(a.to_dict().get("storage_path",""));a.reference.delete()
        ref.delete();return Response(status=204)
    @decorators.action(detail=True,methods=["post"],url_path="attachments")
    def add_attachment(self,r,pk=None):
        mref=col(r.user,"memories").document(pk);m=mref.get()
        if not m.exists:return Response({"detail":"Not found."},404)
        f=r.FILES.get("file")
        if not f:return Response({"detail":"Choose a file."},400)
        ext=os.path.splitext(f.name)[1].lower()
        if ext not in ALLOWED:return Response({"detail":"This file type is not allowed. Use an image, PDF, Word, Excel or text file."},400)
        if f.size>MAX_MB*1024*1024:return Response({"detail":f"Files must be under {MAX_MB} MB."},400)
        if len(list(mref.collection("attachments").stream()))>=MAX_FILES:return Response({"detail":f"A memory can have up to {MAX_FILES} attachments."},400)
        path=f"memories/{r.user.id}/{pk}/{uuid.uuid4().hex}{ext}"
        url=upload_file(f,path,getattr(f,"content_type","application/octet-stream"))
        a={"name":f.name[:200],"size":f.size,"content_type":getattr(f,"content_type","") or "","url":url,"image":ext in IMAGES,"storage_path":path,"created_at":datetime.now().isoformat()}
        aref=mref.collection("attachments").document();aref.set(a);a["id"]=aref.id
        return self.retrieve(r,pk)
    @decorators.action(detail=True,methods=["delete"],url_path=r"attachments/(?P<att>[^/.]+)")
    def remove_attachment(self,r,pk=None,att=None):
        ref=col(r.user,"memories").document(pk).collection("attachments").document(att);d=ref.get()
        if not d.exists:return Response(status=404)
        delete_file(d.to_dict().get("storage_path",""));ref.delete();return Response(status=204)
