import calendar, math
from datetime import date,timedelta
from django.utils import timezone
from firestore_utils import col,doc_data
INCOME={"earning","salary","other_income"}

def rows(user):
    return [doc_data(x) for x in col(user,"transactions").stream()]

def amount(x): return float(x.get("amount",0) or 0)

def totals(user):
    t=rows(user); income=sum(amount(x) for x in t if x.get("kind") in INCOME)
    expenses=sum(amount(x) for x in t if x.get("kind")=="expense")
    added=sum(amount(x) for x in t if x.get("kind")=="saving")
    return {"income":income,"expenses":expenses,"external_savings":added,"current_savings":income-expenses+added}

def work_cost(t):
    return sum(amount(x) for x in t if x.get("kind")=="expense" and str(x.get("category","")).lower() in ("fuel","food"))

def dateof(x):
    try:return date.fromisoformat(str(x.get("date",""))[:10])
    except:return None

def forecast(user):
    today=timezone.localdate(); first=today.replace(day=1); t=rows(user)
    left=calendar.monthrange(today.year,today.month)[1]-today.day+1
    recent=[x for x in t if dateof(x) and today-timedelta(days=60)<=dateof(x)<=today]
    earn=[x for x in recent if x.get("kind")=="earning"]; per={}
    for x in earn:
        d=dateof(x); per[d]=per.get(d,0)+amount(x)
    days=len(per); avg_gross=sum(per.values())/days if days else 0; avg_cost=work_cost(recent)/days if days else 0; avg_net=avg_gross-avg_cost
    tref=col(user,"targets").document(first.isoformat()).get(); target=float((tref.to_dict() or {}).get("amount",0)) if tref.exists else 0
    month=[x for x in t if dateof(x) and dateof(x)>=first]
    earned=sum(amount(x) for x in month if x.get("kind") in INCOME)-work_cost(month)
    remaining=max(target-earned,0); req=remaining/left
    buckets={}
    for d,a in per.items(): buckets.setdefault(d.weekday(),[]).append(a)
    rates=sorted({max(50,round(avg_net*f/50)*50) for f in (.75,1,1.25,1.5)}) if avg_net>0 else [500,600,700,800]
    return {"target":target,"earned_net":earned,"remaining":remaining,"days_left":left,"target_reached":bool(target) and remaining==0,
      "avg_gross":round(avg_gross),"avg_expense":round(avg_cost),"avg_net":round(avg_net),"required_per_day":round(req),
      "days_required":math.ceil(remaining/avg_net) if avg_net>0 else None,"on_track":bool(target) and avg_net>=req,
      "by_weekday":{str(k):round(sum(v)/len(v)) for k,v in buckets.items()},
      "scenarios":[{"per_day":r,"projected_month_end":round(earned+r*left)} for r in rates],"has_data":days>0}

def extras(user):
    today=timezone.localdate(); t=rows(user); months=[]
    for i in (2,1,0):
        m=today.month-i;y=today.year
        while m<1:m+=12;y-=1
        q=[x for x in t if dateof(x) and dateof(x).year==y and dateof(x).month==m]
        inc=sum(amount(x) for x in q if x.get("kind") in INCOME); exp=sum(amount(x) for x in q if x.get("kind")=="expense")
        months.append({"month":f"{y}-{m:02d}","income":inc,"expenses":exp,"saved":inc-exp})
    cats={}
    for x in t:
        d=dateof(x)
        if x.get("kind")=="expense" and d and d>=today.replace(day=1):
            c=x.get("category",""); cats[c]=cats.get(c,0)+amount(x)
    daily={}
    for x in t:
        d=dateof(x)
        if x.get("kind")=="earning" and d and today-timedelta(days=13)<=d<=today: daily[d]=daily.get(d,0)+amount(x)
    return {"months":months,"categories":[{"category":k,"total":v} for k,v in sorted(cats.items(),key=lambda z:-z[1])],
            "daily":[{"date":str(today-timedelta(days=i)),"amount":daily.get(today-timedelta(days=i),0)} for i in range(13,-1,-1)]}
