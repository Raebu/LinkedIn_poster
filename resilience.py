"""Resilience, audit/replay, health, cost and recovery primitives for Social OS."""
from __future__ import annotations
import json,os,hashlib
from pathlib import Path
from datetime import datetime,timezone
OUTBOX=Path(os.getenv("SOCIAL_OUTBOX","/tmp/linkedin-state/social_outbox.jsonl"));SCHEMA_VERSION="2.0"
def now():return datetime.now(timezone.utc).isoformat()
def fingerprint(kind,payload):return hashlib.sha256((kind+json.dumps(payload,sort_keys=True,default=str)).encode()).hexdigest()[:24]
def queue(kind,payload):
 OUTBOX.parent.mkdir(parents=True,exist_ok=True);rec={"id":fingerprint(kind,payload),"at":now(),"kind":kind,"payload":payload};
 with OUTBOX.open("a") as f:f.write(json.dumps(rec,default=str)+"\n")
 return rec["id"]
def pending():
 if not OUTBOX.exists():return []
 seen=set();out=[]
 for line in OUTBOX.read_text().splitlines():
  try:r=json.loads(line)
  except:continue
  if r.get("id") not in seen:seen.add(r.get("id"));out.append(r)
 return out
def clear(ids):
 ids=set(ids)
 if not OUTBOX.exists():return
 keep=[r for r in pending() if r.get("id") not in ids];OUTBOX.write_text("".join(json.dumps(r)+"\n" for r in keep))
def decision_record(action,x,reason,confidence,policy="growth-v2",voice="martin-canonical",model=""):
 return {"at":now(),"action":action,"input":x,"reason":reason,"confidence":confidence,"policy":policy,"voice":voice,"model":model,"schema":SCHEMA_VERSION}
def health(state):
 return {"at":now(),"schema":SCHEMA_VERSION,"relationships":len(state.get("relationships",{})),"actions":len(state.get("growth_actions",[])),"opportunities":len(state.get("opportunities",[])),"outbox":len(pending())}
def usage(state,openai_calls=0,linkedin_calls=0,sheets_calls=0):
 u=state.setdefault("usage",{});u["openai_calls"]=u.get("openai_calls",0)+openai_calls;u["linkedin_calls"]=u.get("linkedin_calls",0)+linkedin_calls;u["sheets_calls"]=u.get("sheets_calls",0)+sheets_calls;u["updated"]=now();return u
