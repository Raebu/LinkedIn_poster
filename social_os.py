"""Cross-platform professional presence intelligence. No platform execution here."""
from __future__ import annotations
import json,math
from collections import Counter
from datetime import datetime,timezone
import gdrive_memory as gm

def now():return datetime.now(timezone.utc).isoformat()
def controls():return {x:gm.control(x) for x in ("Publishing Enabled","Growth Enabled","Comments Enabled","Reactions Enabled","Reshares Enabled")}
def allowed(action):
 c=controls()
 if action=="publish":return c["Publishing Enabled"]
 if not c["Growth Enabled"]:return False
 return {"comment":c["Comments Enabled"],"react":c["Reactions Enabled"],"reshare":c["Reshares Enabled"]}.get(action,True)
def identity_candidates(name,organisation=""):
 out=[]
 for r in gm.rows("Social Identity Map"):
  score=0
  if name and str(r.get("Canonical Name","")).lower()==name.lower():score+=.7
  if organisation and str(r.get("Organisation","")).lower()==organisation.lower():score+=.2
  if score>=.7:out.append((score,r))
 return sorted(out,key=lambda x:x[0],reverse=True)
def source_context():
 return [r for r in gm.rows("Social Sources") if str(r.get("Status","")).upper() in {"VERIFIED","ACTIVE"}]
def incubate(idea,evidence="",platform="LinkedIn",stage="SEED"):
 gm.append("Social Ideas",[now(),now(),idea,stage,evidence,platform,"",""])
def negative(text,kind,reason,correction=""):gm.log_negative("LinkedIn",text,kind,reason,correction)
def network_health(state):
 rels=state.get("relationships",{});acts=state.get("growth_actions",[])[-100:];topics=[a.get("topic") for a in acts if a.get("topic")];orgs=[a.get("organisation") for a in acts if a.get("organisation")]
 diversity=len(set(topics));concentration=(max(Counter(orgs).values())/len(orgs)) if orgs else 0;silence=sum(a.get("action")=="no_action" for a in acts)/len(acts) if acts else 0
 row=[now(),"LinkedIn",len(rels),sum(r.get("interactions",0)==1 for r in rels.values()),sum(r.get("interactions",0)>=5 for r in rels.values()),diversity,round(concentration,3),round(silence,3),len(state.get("opportunities",[]))];gm.append("Social Network Health",row);return row
def digest(state):
 rels=state.get("relationships",{});acts=state.get("growth_actions",[])[-50:];ops=state.get("opportunities",[])
 progressed=sum(1 for r in rels.values() if r.get("stage") in {"ENGAGED","RECURRING","STRONG"});silence=sum(a.get("action")=="no_action" for a in acts)
 text=f"LinkedIn: {len(acts)} recent decisions; {silence} deliberate no-actions; {progressed} developed relationships; {len(ops)} opportunity signals retained."
 gm.log_digest("latest",text);return text
