"""Generate, quality-check and optionally publish a LinkedIn-native Martin Raeburn post."""
from __future__ import annotations
import json,os,random,re
from datetime import datetime,timezone
from openai import OpenAI
from voice import MARTIN_VOICE
from intelligence import load_state,save_state,duplicate,deterministic_gate,content_context
from linkedin_api import LinkedIn

DRY=os.getenv("DRY_RUN","true").lower()=="true"
MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
TOPICS=["AI implementation economics","software architecture and technical debt","automation and human judgement","enterprise adoption friction","technology governance and risk","interoperability and procurement","organisational design and incentives","technology leadership","operational resilience","emerging technology commercialisation","productivity and operational design","market structure and technology"]

def ask(prompt):return OpenAI(api_key=os.environ["OPENAI_API_KEY"]).responses.create(model=MODEL,input=MARTIN_VOICE+"\n\nTASK\n"+prompt).output_text.strip()
def parse(s):
 try:return json.loads(re.sub(r"^```(?:json)?\s*|\s*```$","",s.strip(),flags=re.I))
 except:return None

def generate(s):
 topic=random.choice(TOPICS);recent=content_context(s)
 for _ in range(4):
  raw=ask(f"Create ONE LinkedIn-native original post about {topic}. Recent posts:\n{recent}\nDo not repeat their argument. Return JSON only: {{\"text\":\"...\",\"topic\":\"...\",\"why_worth_saying\":\"...\"}}. Make one non-obvious but defensible observation. Complex thinking, simple language. No invented current facts, statistics, clients or personal anecdotes. Do not depend on current news unless verified context is supplied. Natural paragraphs, not one sentence per line. No question required. 0-2 hashtags only if genuinely useful.")
  d=parse(raw)
  if not d:continue
  text="\n".join(x.strip() for x in str(d.get("text","")).splitlines() if x.strip())
  ok,_=deterministic_gate(text)
  if not ok or duplicate(text,s.get("posts",[])):continue
  review=parse(ask(f"Review this proposed LinkedIn post:\n{text}\nReturn JSON only {{\"pass\":true,\"reason\":\"\"}}. Pass only if it is specific, intellectually useful, natural, reputation-safe, factual without unsupported certainty, complex thinking in simple language, not corporate filler, not generic LinkedIn content, and not political persuasion."))
  if review and review.get("pass") is True:return text,d.get("topic",topic),d.get("why_worth_saying","")
 return None,None,None

def main():
 s=load_state();text,topic,why=generate(s)
 if not text:return print("NO_POST: quality gate found nothing worth publishing")
 print("POST CANDIDATE\n"+text+f"\n\nTOPIC: {topic}\nWHY: {why}\nDRY_RUN={DRY}")
 urn=""
 if not DRY:urn=LinkedIn().create_post(text);print("PUBLISHED",urn)
 s.setdefault("posts",[]).append({"timestamp":datetime.now(timezone.utc).isoformat(),"text":text,"topic":topic,"urn":urn,"dry_run":DRY});s["posts"]=s["posts"][-250:];save_state(s)
if __name__=="__main__":main()
