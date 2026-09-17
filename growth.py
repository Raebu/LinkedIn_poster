"""Relationship-aware LinkedIn growth engine. Official APIs only; writes capability-gated."""
from __future__ import annotations
import json,os,time
from datetime import datetime,timezone
from pathlib import Path
from openai import OpenAI
from voice import MARTIN_VOICE
from intelligence import deterministic_gate,similarity,load_state,save_state
from linkedin_api import growth_client
from growth_intelligence import stage,novelty,expertise,risk,needs_verification,opportunity,value_score,why,update_relationship,weekly_review

QUEUE=Path(os.getenv("GROWTH_QUEUE","growth_queue.json"));DRY=os.getenv("DRY_RUN","true").lower()=="true";MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
COMMUNITY=os.getenv("LINKEDIN_COMMUNITY_LIVE","false").lower()=="true";MAX_ACTIONS=int(os.getenv("GROWTH_MAX_ACTIONS","5"));COOLDOWN_HOURS=int(os.getenv("GROWTH_RELATIONSHIP_COOLDOWN_HOURS","36"));MIN_VALUE=float(os.getenv("GROWTH_MIN_VALUE","0.48"));MIN_NOVELTY=float(os.getenv("GROWTH_MIN_NOVELTY","0.42"))
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
def history_text(rel):return "; ".join(a.get("summary",a.get("action","")) for a in rel.get("history",[])[-6:])

def comment_for(source,rel,state,reply_context=""):
 for _ in range(4):
  t=" ".join(ask(f"Source LinkedIn post/thread:\n{source}\n\nPrior relationship:\n{history_text(rel) or 'None'}\n\nReply context:\n{reply_context or 'None'}\nWrite one useful professional response. Add a genuinely NEW distinction, mechanism, consequence, constraint or counterpoint. Continue the conversation naturally if this is a reply to Martin. Do not flatter, paraphrase, manufacture disagreement or force a question. Complex thinking, simple language. Output only the response or NO_REPLY.").split())
  if t.upper().startswith("NO_REPLY"):return None
  ok,_=deterministic_gate(t)
  if ok and similarity(t.split(".")[0],source)<.56 and novelty(t,state)>=MIN_NOVELTY:return t
 return None

def decide(x,rel,state):
 requested=str(x.get("action") or "auto").lower();source=str(x.get("source_text") or "").strip()
 if requested in {"comment","reshare","react","reaction","no_action"}:return requested
 if not source or value_score(x,rel,state)<MIN_VALUE:return "no_action"
 raw=ask(f"LinkedIn post/thread:\n{source}\n\nRelationship stage: {stage(rel)}\nPrior context: {history_text(rel) or 'None'}\nExpertise position: {expertise(source)}\nRisk: {risk(source)}\nChoose exactly one: NO_ACTION, REACT, COMMENT, RESHARE. Prefer silence unless useful. COMMENT requires new substance. RESHARE requires unusually useful audience value plus Martin's framing. REACT is acknowledgement when words add little. Never manufacture disagreement. Output one label.").strip().lower()
 return {"react":"react","comment":"comment","reshare":"reshare"}.get(raw,"no_action")

def log_action(state,x,action,status,text="",reason=""):
 key=relationship_key(x);rel=state.setdefault("relationships",{}).setdefault(key,{"history":[],"interactions":0,"replies":0});rec={"at":now().isoformat(),"action":action,"status":status,"urn":x.get("urn",""),"why":reason,"organisation":x.get("organisation",""),"topic":x.get("topic","")}
 if text:rec["summary"]=text[:500]
 rel["history"].append(rec);rel["history"]=rel["history"][-50:]
 if status in {"executed","dry_run"}:rel["interactions"]+=1;rel["last_interaction"]=rec["at"]
 update_relationship(rel,x,status);state.setdefault("growth_actions",[]).append({"relationship":key,**rec});state["growth_actions"]=state["growth_actions"][-2000:]

def main():
 q=items();state=load_state();done=[];acted=0;li=None
 for x in q:
  urn=str(x.get("urn") or "").strip();source=str(x.get("source_text") or "").strip();rel=state.setdefault("relationships",{}).setdefault(relationship_key(x),{"history":[],"interactions":0,"replies":0})
  if opportunity(source):
   op={"at":now().isoformat(),"relationship":relationship_key(x),"urn":urn,"source":source[:700],"organisation":x.get("organisation","")}
   if op["source"] and not any(o.get("urn")==urn and urn for o in state.setdefault("opportunities",[])):state["opportunities"].append(op);state["opportunities"]=state["opportunities"][-300:]
  if acted>=MAX_ACTIONS:break
  if recent(rel) and not x.get("reply_to_martin") and not x.get("override_cooldown"):
   reason=why("NO_ACTION",x,rel,state,"cooldown");print("NO_ACTION",urn,reason);log_action(state,x,"no_action","cooldown",reason=reason);done.append(x);continue
  action=decide(x,rel,state);reason=why(action.upper(),x,rel,state)
  if action=="no_action":print("NO_ACTION",urn,reason);log_action(state,x,action,"judgement",reason=reason);done.append(x);continue
  if risk(source)=="high":print("NO_ACTION",urn,"reputation risk gate");log_action(state,x,"no_action","risk_gate",reason=reason);done.append(x);continue
  if not urn:print("DEFER",action,"missing target URN");log_action(state,x,action,"deferred",reason=reason);continue
  text=comment_for(source,rel,state,str(x.get("reply_context") or "")) if source and action in {"comment","reshare"} else ""
  if action in {"comment","reshare"} and source and not text:print("NO_ACTION",urn,"quality/novelty gate");log_action(state,x,"no_action","quality_gate",reason=reason);done.append(x);continue
  if text and needs_verification(text) and not x.get("claims_verified"):
   print("DEFER",action,urn,"factual/current claim requires verification");log_action(state,x,action,"verification_wait",text,reason);continue
  if action in {"comment","react"} and not COMMUNITY:print("READY",action,urn,"waiting for Community Management capability");log_action(state,x,action,"capability_wait",text or "",reason);continue
  status="dry_run" if DRY else "executed";print(action.upper(),urn,text or "",reason)
  if not DRY:
   li=li or growth_client()
   if action=="comment":li.create_comment(urn,text)
   elif action=="react":li.create_reaction(urn,REACTIONS.get(str(x.get("reaction","like")).lower(),"LIKE"))
   elif action=="reshare":li.reshare(urn,text or "")
  log_action(state,x,action,status,text or "",reason);done.append(x);acted+=1;time.sleep(1)
 state["growth_review"]=weekly_review(state);save_state(state)
 if done:QUEUE.write_text(json.dumps([x for x in q if x not in done],indent=2)+"\n")
 print(f"GROWTH_SUMMARY actions={acted} completed={len(done)} remaining={len(q)-len(done)} relationships={len(state.get('relationships',{}))} opportunities={len(state.get('opportunities',[]))} community_live={COMMUNITY} dry_run={DRY}")
if __name__=="__main__":main()
