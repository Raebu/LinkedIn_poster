"""Cross-platform professional presence intelligence and governance."""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone,timedelta
import gdrive_memory as gm
SCHEMA_VERSION="2.0";OPPORTUNITY_STAGES=("SIGNAL","WATCH","QUALIFIED","FOLLOW_UP","CLOSED","ARCHIVED")
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
  score=(.7 if name and str(r.get("Canonical Name","")).lower()==name.lower() else 0)+(.2 if organisation and str(r.get("Organisation","")).lower()==organisation.lower() else 0)
  if score>=.7:out.append((score,r))
 return sorted(out,key=lambda x:x[0],reverse=True)
def source_context():return [r for r in gm.rows("Social Sources") if str(r.get("Status","")).upper() in {"VERIFIED","ACTIVE"}]
def incubate(idea,evidence="",platform="LinkedIn",stage="SEED"):gm.append("Social Ideas",[now(),now(),idea,stage,evidence,platform,"",""])
def negative(text,kind,reason,correction=""):gm.log_negative("LinkedIn",text,kind,reason,correction)
def record_event(entity,event,old="",new="",evidence="",confidence=.7):gm.append("Social Events",[now(),entity,event,old,new,evidence,confidence])
def contradiction(entity,field,stored,observed,evidence=""):gm.append("Social Contradictions",[now(),entity,field,stored,observed,evidence,"OPEN"])
def uncertainty(subject,unknown,needed_for=""):gm.append("Social Uncertainty",[now(),subject,unknown,needed_for,"OPEN"])
def research_required(question,reason,source="",priority="NORMAL"):gm.append("Social Research Queue",[now(),question,reason,source,priority,"QUEUED","",""])
def lineage(content_id,idea,evidence,conversations=""):gm.append("Social Content Lineage",[now(),content_id,idea,evidence,conversations])
def position(topic,statement,evidence="",supersedes=""):gm.append("Social Positions",[now(),topic,statement,evidence,supersedes,"ACTIVE"])
def contact_fatigue(rel):
 try:
  cutoff=datetime.now(timezone.utc)-timedelta(days=30);dates=[datetime.fromisoformat(x.get("at")) for x in rel.get("history",[]) if x.get("at")]
  n=sum(d>=cutoff for d in dates);return min(1,n/10)
 except:return 0
def reciprocal_stage(rel):
 n=int(rel.get("interactions",0));replies=int(rel.get("replies",0));return "STRONG" if n>=8 and replies>=3 else "RECURRING" if n>=5 and replies>=2 else "ENGAGED" if replies>=1 or n>=2 else "FAMILIAR" if n else "DISCOVERED"
def conversation_closed(text):return str(text).strip().lower() in {"thanks","thanks martin","thank you","cheers","appreciate it","👍","🙏"}
def opportunity_stage(signals):return "QUALIFIED" if signals>=2 else "WATCH" if signals==1 else "SIGNAL"
def human_corrections():return gm.rows("Social Human Corrections")
def duplicate_recent(text,days=14):
 from intelligence import similarity
 candidates=[]
 for tab,col in (("Posts","Text"),("Social Ideas","Idea")):
  for r in gm.rows(tab):
   if r.get(col):candidates.append(str(r[col]))
 return max([similarity(text,x) for x in candidates] or [0])>.72
def network_health(state):
 rels=state.get("relationships",{});acts=state.get("growth_actions",[])[-100:];topics=[a.get("topic") for a in acts if a.get("topic")];orgs=[a.get("organisation") for a in acts if a.get("organisation")];diversity=len(set(topics));concentration=max(Counter(orgs).values())/len(orgs) if orgs else 0;silence=sum(a.get("action")=="no_action" for a in acts)/len(acts) if acts else 0
 row=[now(),"LinkedIn",len(rels),sum(r.get("interactions",0)==1 for r in rels.values()),sum(reciprocal_stage(r) in {"RECURRING","STRONG"} for r in rels.values()),diversity,round(concentration,3),round(silence,3),len(state.get("opportunities",[]))];gm.append("Social Network Health",row);return row
def digest(state):
 rels=state.get("relationships",{});acts=state.get("growth_actions",[])[-50:];ops=state.get("opportunities",[]);progressed=sum(reciprocal_stage(r) in {"ENGAGED","RECURRING","STRONG"} for r in rels.values());silence=sum(a.get("action")=="no_action" for a in acts);text=f"LinkedIn: {len(acts)} recent decisions; {silence} deliberate no-actions; {progressed} reciprocal/developed relationships; {len(ops)} opportunity signals retained.";gm.log_digest("latest",text);return text
