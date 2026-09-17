"""Generate, quality-check and optionally publish varied LinkedIn-native Martin Raeburn content."""
from __future__ import annotations
import json,os,random,re
from datetime import datetime,timezone
from openai import OpenAI
from voice import MARTIN_VOICE
from intelligence import load_state,save_state,duplicate,deterministic_gate,content_context
from linkedin_api import LinkedIn
from media import render_visual,render_document

DRY=os.getenv("DRY_RUN","true").lower()=="true";MODEL=os.getenv("OPENAI_MODEL","gpt-5-mini")
TOPICS=["AI implementation economics","software architecture and technical debt","automation and human judgement","enterprise adoption friction","technology governance and risk","interoperability and procurement","organisational design and incentives","technology leadership","operational resilience","emerging technology commercialisation","productivity and operational design","market structure and technology"]
FORMATS={"short_insight":"60-130 words. One sharp observation, mechanism or consequence. Stop when the idea is complete.","standard":"150-300 words. Develop one argument with enough explanation to make it useful, without turning it into an essay.","deep_dive":"400-800 words. White-paper-style depth only when the idea genuinely needs several linked mechanisms, trade-offs or implications. Use readable paragraphs and concrete language; depth must come from reasoning, not padding.","visual":"80-220 words plus a precise visual brief for an original diagram, framework, architecture, chart concept or conceptual graphic that adds information rather than decoration.","document":"100-220 word caption plus a 5-8 page/slide document outline for a framework, technical explanation, comparison or research-led idea. Each page must earn its place.","conversation":"80-220 words. Establish a substantive observation or unresolved problem first, then ask one informed question that invites evidence, mechanisms, implementation detail or a real trade-off. Never engagement bait."}
def ask(prompt):return OpenAI(api_key=os.environ["OPENAI_API_KEY"]).responses.create(model=MODEL,input=MARTIN_VOICE+"\n\nTASK\n"+prompt).output_text.strip()
def parse(s):
 try:return json.loads(re.sub(r"^```(?:json)?\s*|\s*```$","",s.strip(),flags=re.I))
 except:return None
def choose_plan(topic,recent):
 spec="\n".join(f"- {k}: {v}" for k,v in FORMATS.items());d=parse(ask(f"Decide the best LinkedIn treatment for an original idea in '{topic}'. Recent content:\n{recent}\nAvailable formats:\n{spec}\nChoose the medium AFTER deciding what is worth saying. Do not manufacture depth or a visual merely for variety. Return JSON only: {{\"format\":\"short_insight|standard|deep_dive|visual|document|conversation\",\"angle\":\"one precise non-obvious defensible idea\",\"reason\":\"why this format earns its use\"}}.")) or {};fmt=d.get("format")
 if fmt not in FORMATS:fmt=random.choice(["short_insight","standard","deep_dive"])
 return fmt,str(d.get("angle",topic)),str(d.get("reason",""))
def generate(s):
 topic=random.choice(TOPICS);recent=content_context(s);fmt,angle,format_reason=choose_plan(topic,recent)
 for _ in range(4):
  d=parse(ask(f"Create ONE LinkedIn-native original post. Topic: {topic}. Chosen angle: {angle}. Format: {fmt}. Format rule: {FORMATS[fmt]} Recent posts:\n{recent}\nDo not repeat their argument. Return JSON only: {{\"text\":\"...\",\"topic\":\"...\",\"why_worth_saying\":\"...\",\"visual_brief\":\"\",\"document_outline\":[]}}. Complex thinking, simple language. One coherent argument. No invented current facts, statistics, clients, transactions, meetings, product use or personal anecdotes. Do not depend on current news unless verified context is supplied. Natural paragraphs. No generic hook, generic concluding question or corporate filler. 0-2 hashtags only if genuinely useful. For visual, visual_brief must specify the information the diagram communicates, not decorative imagery. For document, document_outline must contain 5-8 concise page concepts. Otherwise leave asset fields empty."))
  if not d:continue
  text="\n".join(x.strip() for x in str(d.get("text","")).splitlines() if x.strip());words=len(text.split());bounds={"short_insight":(45,155),"standard":(120,340),"deep_dive":(330,900),"visual":(60,260),"document":(70,270),"conversation":(60,260)}[fmt]
  if not bounds[0]<=words<=bounds[1]:continue
  ok,_=deterministic_gate(text)
  if not ok or duplicate(text,s.get("posts",[])):continue
  if fmt=="visual" and len(str(d.get("visual_brief","")))<=40:continue
  if fmt=="document" and not 5<=len(d.get("document_outline",[]))<=8:continue
  review=parse(ask(f"Review this proposed LinkedIn {fmt} post:\n{text}\nReturn JSON only {{\"pass\":true,\"reason\":\"\"}}. Judge it AS the chosen format. Pass only if the format is justified, every paragraph earns its place, it is specific, intellectually useful, natural, reputation-safe, factual without unsupported certainty, complex thinking in simple language, not corporate filler, not generic LinkedIn content, and not political persuasion."))
  if review and review.get("pass") is True:return text,d.get("topic",topic),d.get("why_worth_saying",""),fmt,d.get("visual_brief",""),d.get("document_outline",[]),format_reason
 return (None,)*7
def main():
 s=load_state();text,topic,why,fmt,visual,document,format_reason=generate(s)
 if not text:return print("NO_POST: quality gate found nothing worth publishing")
 print("POST CANDIDATE\n"+text+f"\n\nFORMAT: {fmt}\nTOPIC: {topic}\nWHY: {why}\nFORMAT_REASON: {format_reason}")
 asset_bytes=None;alt=""
 if fmt=="visual":asset_bytes,alt=render_visual(visual,topic);print(f"VISUAL_RENDERED: {len(asset_bytes)} bytes\nALT: {alt}")
 elif fmt=="document":asset_bytes=render_document(document,topic);print(f"DOCUMENT_RENDERED: {len(asset_bytes)} bytes, {len(document)} pages")
 print(f"DRY_RUN={DRY}");urn="";asset_urn=""
 if not DRY:
  li=LinkedIn()
  if fmt=="visual":urn,asset_urn=li.create_image_post(text,asset_bytes,alt)
  elif fmt=="document":urn,asset_urn=li.create_document_post(text,asset_bytes,title=f"{topic.title()} — Martin Raeburn.pdf")
  else:urn=li.create_post(text)
  print("PUBLISHED",urn,"ASSET",asset_urn)
 s.setdefault("posts",[]).append({"timestamp":datetime.now(timezone.utc).isoformat(),"text":text,"topic":topic,"format":fmt,"visual_brief":visual,"document_outline":document,"urn":urn,"asset_urn":asset_urn,"dry_run":DRY});s["posts"]=s["posts"][-250:];save_state(s)
if __name__=="__main__":main()
