"""Shared durable social-agent memory for Martin Raeburn."""
from __future__ import annotations
import json,os,time
from datetime import datetime,timezone
SHEET_ID=os.getenv("SOCIAL_MEMORY_SHEET_ID") or os.getenv("BSKY_MEMORY_SHEET_ID") or "1yIwJqlmgRbp1_o4MFCLHMSOOgaE3DYMd31eF43dF9bs";_CACHE={};_BOOK=None;CACHE_SECONDS=int(os.getenv("GDRIVE_CACHE_SECONDS","300"))
TABS={
"LinkedIn Relationships":["Updated","Key","Name","Profile URL","Organisation","Stage","Objective","Confidence","Interactions","Replies","Topics","Last Interaction","Fresh Until"],"LinkedIn Interactions":["At","Action","Status","Relationship","URN","Organisation","Topic","Text","Why","Confidence"],"LinkedIn Conversations":["At","Relationship","URN","Direction","Their Text","Martin Reply","Context"],"LinkedIn Opportunities":["At","Relationship","URN","Organisation","Source","Stage","Evidence","Next Review"],"LinkedIn Target Accounts":["Added","Name","Profile URL","Organisation","Category","Priority","Objective","Notes","Active"],"LinkedIn Performance":["At","URN","Relationship","Reactions","Comments","Reshares","Conversation Depth","Relationship Change","Notes"],"LinkedIn Agent Runs":["Started","Finished","Mode","Dry Run","Actions","Relationships","Opportunities","Notes"],"LinkedIn Weekly Reviews":["At","Review JSON"],
"Social Identity Map":["Person ID","Canonical Name","LinkedIn","Bluesky","Organisation","Confidence","Evidence","Last Verified"],"Social Knowledge Graph":["Updated","Concept","Related Concepts","Evidence","Platforms","Strength","Status"],"Social Ideas":["Created","Updated","Idea","Stage","Evidence","Platforms","Last Used","Notes"],"Social Sources":["Added","Claim","Source URL","Publisher","Checked","Recheck","Confidence","Status"],"Social Audience Learning":["Updated","Audience","Topic","Format","Signal","Evidence","Do Not Optimise Opinion"],"Social Negative Learning":["At","Platform","Text","Failure Type","Reason","Correction"],"Social Experiments":["Started","Platform","Hypothesis","Variable","Control","Result","Status","Guardrail"],"Social Network Health":["At","Platform","Relationships","New Conversations","Recurring Conversations","Topic Diversity","Concentration","Silence Rate","Opportunities"],"Social Controls":["Control","Value","Updated","Notes"],"Social Executive Digests":["At","Period","Summary"],
"Social Events":["At","Entity","Event","Old","New","Evidence","Confidence"],"Social Contradictions":["At","Entity","Field","Stored","Observed","Evidence","Status"],"Social Uncertainty":["At","Subject","Unknown","Needed For","Status"],"Social Research Queue":["At","Question","Reason","Source","Priority","Status","Findings","Evidence"],"Social Content Lineage":["At","Content ID","Idea","Evidence","Conversations"],"Social Positions":["At","Topic","Position","Evidence","Supersedes","Status"],"Social Human Corrections":["At","Entity","Field","Correct Value","Reason","Active"],"Social Decision Replay":["At","Decision ID","Platform","Action","Input JSON","Reason","Confidence","Policy","Voice","Model","Schema"],"Social Policy Registry":["At","Policy","Version","Voice","Model","Thresholds","Status"],"Social Health":["At","Schema","Relationships","Actions","Opportunities","Outbox","OAuth","Sheets","Notes"],"Social Usage":["At","OpenAI Calls","LinkedIn Calls","Sheets Calls","Estimated Cost","Notes"],"Social Schema":["Version","Applied","Notes"],"Social Backups":["At","Snapshot ID","Location","Status","Notes"]}
DEFAULT_CONTROLS=[("Publishing Enabled","TRUE","Global publishing kill switch"),("Growth Enabled","TRUE","Global growth kill switch"),("Comments Enabled","TRUE","Comment execution"),("Reactions Enabled","TRUE","Reaction execution"),("Reshares Enabled","TRUE","Reshare execution"),("Research Enabled","TRUE","Allow research queueing; research execution requires an approved source")]
def now():return datetime.now(timezone.utc).isoformat()
def _client():
 global _BOOK
 if _BOOK is not None:return _BOOK
 raw=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
 if not raw or not SHEET_ID:return None
 import gspread
 from google.oauth2.service_account import Credentials
 creds=Credentials.from_service_account_info(json.loads(raw),scopes=["https://www.googleapis.com/auth/spreadsheets"]);_BOOK=gspread.authorize(creds).open_by_key(SHEET_ID);return _BOOK
def enabled():return bool(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") and SHEET_ID)
def ensure_tabs():
 b=_client()
 if not b:return
 existing={s.title for s in b.worksheets()}
 for name,headers in TABS.items():
  if name not in existing:w=b.add_worksheet(title=name,rows=1000,cols=max(14,len(headers)));w.append_row(headers,value_input_option="RAW")
 if not b.worksheet("Social Controls").get_all_records():
  for c,v,n in DEFAULT_CONTROLS:b.worksheet("Social Controls").append_row([c,v,now(),n],value_input_option="RAW")
 if not b.worksheet("Social Schema").get_all_records():b.worksheet("Social Schema").append_row(["2.0",now(),"Cross-platform Social OS governance schema"],value_input_option="RAW")
def append(tab,row):
 try:
  ensure_tabs();b=_client()
  if b:b.worksheet(tab).append_row(["" if x is None else str(x) for x in row],value_input_option="RAW");_CACHE.pop(tab,None)
 except Exception as e:print("GDRIVE append failed",tab,e)
def rows(tab,refresh=False):
 try:
  ts,data=_CACHE.get(tab,(0,None))
  if not refresh and data is not None and time.monotonic()-ts<CACHE_SECONDS:return data
  ensure_tabs();b=_client();data=b.worksheet(tab).get_all_records() if b else [];_CACHE[tab]=(time.monotonic(),data);return data
 except Exception as e:print("GDRIVE read failed",tab,e);return _CACHE.get(tab,(0,[]))[1] or []
def control(name,default=True):
 for r in rows("Social Controls"):
  if str(r.get("Control","")).strip().lower()==name.lower():return str(r.get("Value","")).lower() in {"true","1","yes","on","enabled"}
 return default
def shared_do_not_engage():
 out=set()
 for r in rows("Do Not Engage"):
  if str(r.get("Active","")).lower() not in {"false","0","no","inactive"}:
   v=str(r.get("DID/Handle/Domain","")).strip().lower()
   if v:out.add(v)
 return out
def verified_knowledge():return [str(r.get("Fact","")) for r in rows("Verified Knowledge") if str(r.get("Status","")).upper()=="VERIFIED"]
def target_accounts():return [r for r in rows("LinkedIn Target Accounts") if str(r.get("Active","true")).lower() not in {"false","0","no","inactive"}]
def log_interaction(r):append("LinkedIn Interactions",[r.get("at"),r.get("action"),r.get("status"),r.get("relationship"),r.get("urn"),r.get("organisation"),r.get("topic"),r.get("summary",""),r.get("why",""),r.get("confidence","")])
def log_opportunity(o):append("LinkedIn Opportunities",[o.get("at"),o.get("relationship"),o.get("urn"),o.get("organisation"),o.get("source"),o.get("stage","SIGNAL"),o.get("evidence",""),o.get("next_review","")])
def log_run(started,dry,state,actions,notes=""):append("LinkedIn Agent Runs",[started,now(),"growth",dry,actions,len(state.get("relationships",{})),len(state.get("opportunities",[])),notes])
def log_review(review):append("LinkedIn Weekly Reviews",[now(),json.dumps(review,ensure_ascii=False)])
def log_negative(platform,text,kind,reason,correction=""):append("Social Negative Learning",[now(),platform,text,kind,reason,correction])
def log_digest(period,summary):append("Social Executive Digests",[now(),period,summary])
