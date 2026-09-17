"""Relationship-aware LinkedIn growth engine.

Discovery/intelligence is independent from execution. The engine never scrapes and
never invents feed access. It can act on trusted post URNs/content supplied by an
approved discovery source. Community Management writes are capability-gated.
"""
from __future__ import annotations
import json,os,time
from datetime import datetime,timezone
from pathlib import Path
from openai import OpenAI
from voice import MARTIN_VOICE
from intelligence import deterministic_gate,similarity,load_state,save_state
from linkedin_api import growth_client

QUEUE=Path(os.getenv("GROWTH_QUEUE","growth_queue.json"))
DRY=os.getenv("DRY_RUN","true").lower()=="true"
MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
COMMUNITY=os.getenv("LINKEDIN_COMMUNITY_LIVE","false").lower()=="true"
MAX_ACTIONS=int(os.getenv("GROWTH_MAX_ACTIONS","5"))
COOLDOWN_HOURS=int(os.getenv("GROWTH_RELATIONSHIP_COOLDOWN_HOURS","36"))
REACTIONS={"like":"LIKE","praise":"PRAISE","empathy":"EMPATHY","interest":"INTEREST","appreciation":"APPRECIATION","entertainment":"ENTERTAINMENT"}

def now():return datetime.now(timezone.utc)
def ask(p):return OpenAI(api_key=os.environ["OPENAI_API_KEY"]).responses.create(model=MODEL,input=MARTIN_VOICE+"\nTASK\n"+p).output_text.strip()
def items():
 try:
  x=json.loads(QUEUE.read_text());return x if isinstance(x,list) else []
 except:return []
def relationship_key(x):return str(x.get("author_urn") or x.get("author") or x.get("profile_url") or x.get("urn") or "unknown")
def recent(rel):
 try:return (now()-datetime.fromisoformat(rel["last_interaction"])).total_seconds()<COOLDOWN_HOURS*3600
 except:return False

def comment_for(source,history=""):
 for _ in range(4):
  t=" ".join(ask(f"Source LinkedIn post:\n{source}\n\nRelevant prior relationship context:\n{history or 'None'}\nWrite one useful professional comment. Add a NEW distinction, mechanism, consequence, constraint or counterpoint; do not paraphrase the source. Complex thinking, simple language. Do not flatter for the sake of engagement. Ask a precise question only if it improves the conversation. Output only comment or NO_REPLY.").split())
  if t.upper().startswith("NO_REPLY"):return None
  ok,_=deterministic_gate(t)
  if ok and similarity(t.split(".")[0],source)<.56:return t
 return None

def decide(x,rel):
 requested=str(x.get("action") or "auto").lower()
 source=str(x.get("source_text") or "").strip()
 if requested in {"comment","reshare","react","reaction","no_action"}:return requested
 if not source:return "no_action"
 history="; ".join(a.get("summary",a.get("action","")) for a in rel.get("history",[])[-4:])
 raw=ask(f"LinkedIn post:\n{source}\n\nRelationship history:\n{history or 'None'}\nChoose exactly one action: NO_ACTION, REACT, COMMENT, RESHARE. Prefer NO_ACTION unless Martin has something genuinely useful to add. COMMENT only for a substantive new contribution. RESHARE only when the post is unusually useful to Martin's professional audience and his added framing would improve it. REACT for worthwhile acknowledgement where a comment would add little. Output one label only.").strip().lower()
 return {"react":"react","comment":"comment","reshare":"reshare"}.get(raw,"no_action")

def log_action(state,x,action,status,text=""):
 key=relationship_key(x);rels=state.setdefault("relationships",{});rel=rels.setdefault(key,{"history":[],"interactions":0})
 rec={"at":now().isoformat(),"action":action,"status":status,"urn":x.get("urn","")}
 if text:rec["summary"]=text[:300]
 rel["history"].append(rec);rel["history"]=rel["history"][-30:]
 if status in {"executed","dry_run"}:
  rel["interactions"]+=1;rel["last_interaction"]=rec["at"]
 state.setdefault("growth_actions",[]).append({"relationship":key,**rec});state["growth_actions"]=state["growth_actions"][-1000:]

def main():
 q=items();state=load_state();done=[];acted=0;li=None
 for x in q:
  urn=str(x.get("urn") or "").strip();source=str(x.get("source_text") or "").strip();key=relationship_key(x)
  rel=state.setdefault("relationships",{}).setdefault(key,{"history":[],"interactions":0})
  if acted>=MAX_ACTIONS:break
  if recent(rel) and not x.get("override_cooldown"):
   print("NO_ACTION",urn,"relationship cooldown");log_action(state,x,"no_action","cooldown");done.append(x);continue
  action=decide(x,rel)
  if action=="no_action":
   print("NO_ACTION",urn);log_action(state,x,action,"judgement");done.append(x);continue
  if not urn:
   print("DEFER",action,"missing target URN");log_action(state,x,action,"deferred");continue
  history="; ".join(a.get("summary",a.get("action","")) for a in rel.get("history",[])[-4:])
  text=comment_for(source,history) if source and action in {"comment","reshare"} else ""
  if action=="comment" and not text:
   print("NO_ACTION",urn,"comment quality gate");log_action(state,x,"no_action","quality_gate");done.append(x);continue
  if action=="reshare" and source and not text:
   print("NO_ACTION",urn,"reshare commentary quality gate");log_action(state,x,"no_action","quality_gate");done.append(x);continue
  if action in {"comment","react"} and not COMMUNITY:
   print("READY",action,urn,"waiting for Community Management approval/token");log_action(state,x,action,"capability_wait",text or "");continue
  status="dry_run" if DRY else "executed"
  print(action.upper(),urn,text or "")
  if not DRY:
   li=li or growth_client()
   if action=="comment":li.create_comment(urn,text)
   elif action=="react":li.create_reaction(urn,REACTIONS.get(str(x.get("reaction","like")).lower(),"LIKE"))
   elif action=="reshare":li.reshare(urn,text or "")
  log_action(state,x,action,status,text or "");done.append(x);acted+=1;time.sleep(1)
 save_state(state)
 if done:QUEUE.write_text(json.dumps([x for x in q if x not in done],indent=2)+"\n")
 print(f"GROWTH_SUMMARY actions={acted} completed={len(done)} remaining={len(q)-len(done)} community_live={COMMUNITY} dry_run={DRY}")
if __name__=="__main__":main()
