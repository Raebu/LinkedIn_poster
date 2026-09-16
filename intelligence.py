"""Content intelligence, memory and deterministic safety gates."""
from __future__ import annotations
import json,math,os,re
from collections import Counter
from pathlib import Path
STATE=Path(os.getenv("STATE_FILE","state.json"))
BANNED=("great insight","absolutely","couldn't agree more","this is so important","spot on","in today's rapidly evolving landscape","the uncomfortable truth nobody wants to hear")
CORP=("game-changing","transformative journey","paradigm shift","dynamic landscape","harness the power","synergise","cutting-edge solutions","navigate complexity","empower organisations")

def load_state():
 try:return json.loads(STATE.read_text())
 except:return {"posts":[],"actions":[],"topics":{},"relationships":{}}
def save_state(s):STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
def toks(t):return re.findall(r"[a-z0-9]+",(t or "").lower())
def similarity(a,b):
 A=Counter(toks(a));B=Counter(toks(b));
 if not A or not B:return 0.0
 return sum(A[k]*B[k] for k in A)/(math.sqrt(sum(v*v for v in A.values()))*math.sqrt(sum(v*v for v in B.values())))
def duplicate(text,posts,threshold=.68):return any(similarity(text,p.get("text",""))>=threshold for p in posts[-80:])
def deterministic_gate(text):
 t=" ".join((text or "").split());low=t.lower()
 if not t or t.upper()=="NO_REPLY":return False,"empty"
 if any(low.startswith(x) for x in BANNED):return False,"generic opening"
 if any(x in low for x in CORP):return False,"corporate filler"
 if len(re.findall(r"#[\w-]+",t))>2:return False,"too many hashtags"
 if "thoughts?" in low:return False,"generic engagement bait"
 return True,"ok"

def content_context(s):
 recent=s.get("posts",[])[-20:]
 return "\n".join(f"- {p.get('topic','')}: {p.get('text','')[:280]}" for p in recent) or "- none"
