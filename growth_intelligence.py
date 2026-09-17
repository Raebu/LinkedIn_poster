"""Strategic intelligence for Martin Raeburn's LinkedIn growth agent.

Pure decision-support layer: relationship progression, novelty, expertise/risk,
network diversity, opportunity detection, action value, audit reasons and reviews.
Execution remains permission-gated in growth.py.
"""
from __future__ import annotations
import re
from collections import Counter
from datetime import datetime,timezone
from intelligence import similarity

STAGES=("DISCOVERED","FAMILIAR","ENGAGED","RECURRING","STRONG")
SENSITIVE=re.compile(r"\b(election|vote|candidate|party|war|terror|suicide|diagnos|medical|lawsuit|fraud|criminal|allegation|breaking news)\b",re.I)
CURRENT_CLAIM=re.compile(r"\b(today|yesterday|this week|currently|latest|just announced|\d+(?:\.\d+)?%|£\d|\$\d)\b",re.I)
OPPORTUNITY=re.compile(r"\b(partner|partnership|speaker|speaking|conference|invest|investment|acquisition|acquire|M&A|vendor|supplier|collaborat|pilot|procurement|RFP|tender)\b",re.I)
EXPERTISE=("AI","automation","software","technology","enterprise","commercial","digital assets","blockchain","M&A","industrial","systems","governance")

def stage(rel):
 n=int(rel.get("interactions",0));replies=int(rel.get("replies",0))
 if n>=8 and replies>=3:return "STRONG"
 if n>=5 and replies>=2:return "RECURRING"
 if n>=2 or replies>=1:return "ENGAGED"
 if n>=1:return "FAMILIAR"
 return "DISCOVERED"

def novelty(text,state):
 old=[a.get("summary","") for a in state.get("growth_actions",[])[-200:] if a.get("summary")]
 return 1.0-max([similarity(text,o) for o in old] or [0.0])

def expertise(source):
 s=source.lower();hits=sum(1 for x in EXPERTISE if x.lower() in s)
 return "confident" if hits>=2 else "explore" if hits else "outside"

def risk(source):
 return "high" if SENSITIVE.search(source) else "normal"

def needs_verification(text):return bool(CURRENT_CLAIM.search(text))
def opportunity(source):return bool(OPPORTUNITY.search(source))

def diversity_penalty(x,state):
 recent=state.get("growth_actions",[])[-40:]
 org=str(x.get("organisation") or "").lower();topic=str(x.get("topic") or "").lower()
 p=0.0
 if org and sum(str(a.get("organisation","")).lower()==org for a in recent)>=4:p+=.25
 if topic and sum(str(a.get("topic","")).lower()==topic for a in recent)>=10:p+=.2
 return min(p,.4)

def value_score(x,rel,state):
 source=str(x.get("source_text") or "")
 score=.45
 if expertise(source)=="confident":score+=.18
 elif expertise(source)=="outside":score-=.15
 if opportunity(source):score+=.12
 if stage(rel) in {"ENGAGED","RECURRING","STRONG"}:score+=.10
 if risk(source)=="high":score-=.30
 score-=diversity_penalty(x,state)
 return max(0.0,min(1.0,score))

def why(action,x,rel,state,extra=""):
 bits=[f"action={action}",f"relationship={stage(rel)}",f"value={value_score(x,rel,state):.2f}",f"expertise={expertise(str(x.get('source_text') or ''))}",f"risk={risk(str(x.get('source_text') or ''))}"]
 if opportunity(str(x.get("source_text") or "")):bits.append("opportunity_signal=yes")
 if extra:bits.append(extra)
 return "; ".join(bits)

def update_relationship(rel,x,status):
 rel["stage"]=stage(rel)
 if x.get("reply_to_martin"):rel["replies"]=int(rel.get("replies",0))+1
 for k in ("author","author_urn","profile_url","organisation"):
  if x.get(k):rel[k]=x[k]
 topics=rel.setdefault("topics",[])
 if x.get("topic") and x["topic"] not in topics:topics.append(x["topic"])
 rel["topics"]=topics[-20:]
 if status in {"executed","dry_run"}:rel["stage"]=stage(rel)

def weekly_review(state):
 acts=state.get("growth_actions",[])[-200:]
 counts=Counter(a.get("action","unknown") for a in acts)
 relationships=state.get("relationships",{})
 stages=Counter(stage(r) for r in relationships.values())
 return {"generated_at":datetime.now(timezone.utc).isoformat(),"actions":dict(counts),"relationship_stages":dict(stages),"relationships":len(relationships),"opportunities":len(state.get("opportunities",[]))}
