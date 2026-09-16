"""Permission-aware growth actions.

The current open LinkedIn permission (w_member_social) can write posts/comments/likes,
but general member-feed reading is restricted. This module therefore never scrapes.
It operates on explicitly supplied, trusted target URNs and source text when available.
"""
from __future__ import annotations
import json,os,re
from pathlib import Path
from openai import OpenAI
from voice import MARTIN_VOICE
from intelligence import deterministic_gate,similarity,load_state,save_state
from linkedin_api import LinkedIn
QUEUE=Path(os.getenv("GROWTH_QUEUE","growth_queue.json"));DRY=os.getenv("DRY_RUN","true").lower()=="true";MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")

def ask(p):return OpenAI(api_key=os.environ["OPENAI_API_KEY"]).responses.create(model=MODEL,input=MARTIN_VOICE+"\nTASK\n"+p).output_text.strip()
def items():
 try:return json.loads(QUEUE.read_text())
 except:return []
def comment_for(source):
 for _ in range(4):
  t=" ".join(ask(f"Source LinkedIn post:\n{source}\nWrite one useful professional comment. Add a NEW distinction, mechanism, consequence, constraint or counterpoint; do not paraphrase the source. Complex thinking, simple language. Ask a precise question only if it improves the conversation. Output only comment or NO_REPLY.").split())
  ok,_=deterministic_gate(t)
  if t.upper().startswith("NO_REPLY"):return None
  if ok and similarity(t.split(".")[0],source)<.56:return t
 return None

def main():
 q=items();s=load_state();li=None if DRY else LinkedIn();done=[]
 for x in q:
  action=x.get("action");urn=x.get("urn","");source=x.get("source_text","")
  # Reshare is supported by the Posts API when a valid source URN is supplied.
  if action=="reshare" and urn:
   commentary=comment_for(source) if source else ""
   print("RESHARE",urn,commentary or "")
   if not DRY:li.reshare(urn,commentary or "")
   done.append(x);continue
  # Comment/reaction hooks are intentionally not guessed: Social Actions access varies by product/version.
  # Keep targets queued until the app has the corresponding endpoint permission verified.
  print("DEFER",action,urn,"requires verified Social Actions capability or source context")
 s.setdefault("actions",[]).extend({"action":x.get("action"),"urn":x.get("urn"),"dry_run":DRY} for x in done);s["actions"]=s["actions"][-500:];save_state(s)
 if done:QUEUE.write_text(json.dumps([x for x in q if x not in done],indent=2)+"\n")
if __name__=="__main__":main()
