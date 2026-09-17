"""LinkedIn durable memory in Martin's shared social-agent Google workbook."""
from __future__ import annotations
import json,os,time
from datetime import datetime,timezone
SHEET_ID=os.getenv("SOCIAL_MEMORY_SHEET_ID") or os.getenv("BSKY_MEMORY_SHEET_ID") or "1yIwJqlmgRbp1_o4MFCLHMSOOgaE3DYMd31eF43dF9bs"
_CACHE={};_BOOK=None;CACHE_SECONDS=int(os.getenv("GDRIVE_CACHE_SECONDS","300"))
TABS={
 "LinkedIn Relationships":["Updated","Key","Name","Profile URL","Organisation","Stage","Interactions","Replies","Topics","Last Interaction"],
 "LinkedIn Interactions":["At","Action","Status","Relationship","URN","Organisation","Topic","Text","Why"],
 "LinkedIn Conversations":["At","Relationship","URN","Direction","Their Text","Martin Reply","Context"],
 "LinkedIn Opportunities":["At","Relationship","URN","Organisation","Source","Status"],
 "LinkedIn Target Accounts":["Added","Name","Profile URL","Organisation","Category","Priority","Notes","Active"],
 "LinkedIn Performance":["At","URN","Relationship","Reactions","Comments","Reshares","Notes"],
 "LinkedIn Agent Runs":["Started","Finished","Mode","Dry Run","Actions","Relationships","Opportunities","Notes"],
 "LinkedIn Weekly Reviews":["At","Review JSON"]}
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
 book=_client()
 if not book:return
 existing={s.title for s in book.worksheets()}
 for name,headers in TABS.items():
  if name not in existing:
   ws=book.add_worksheet(title=name,rows=1000,cols=max(12,len(headers)));ws.append_row(headers,value_input_option="RAW")
def append(tab,row):
 try:
  ensure_tabs();book=_client()
  if book:book.worksheet(tab).append_row(["" if x is None else str(x) for x in row],value_input_option="RAW");_CACHE.pop(tab,None)
 except Exception as e:print("GDRIVE append failed",tab,e)
def rows(tab,refresh=False):
 try:
  ts,data=_CACHE.get(tab,(0,None))
  if not refresh and data is not None and time.monotonic()-ts<CACHE_SECONDS:return data
  ensure_tabs();book=_client();data=book.worksheet(tab).get_all_records() if book else [];_CACHE[tab]=(time.monotonic(),data);return data
 except Exception as e:print("GDRIVE read failed",tab,e);return _CACHE.get(tab,(0,[]))[1] or []
def shared_do_not_engage():
 out=set()
 for r in rows("Do Not Engage"):
  if str(r.get("Active","")).lower() not in {"false","0","no","inactive"}:
   v=str(r.get("DID/Handle/Domain","")).strip().lower()
   if v:out.add(v)
 return out
def verified_knowledge():return [str(r.get("Fact","")) for r in rows("Verified Knowledge") if str(r.get("Status","")).upper()=="VERIFIED"]
def target_accounts():return [r for r in rows("LinkedIn Target Accounts") if str(r.get("Active","true")).lower() not in {"false","0","no","inactive"}]
def log_interaction(rec):append("LinkedIn Interactions",[rec.get("at"),rec.get("action"),rec.get("status"),rec.get("relationship"),rec.get("urn"),rec.get("organisation"),rec.get("topic"),rec.get("summary",""),rec.get("why","")])
def log_opportunity(o):append("LinkedIn Opportunities",[o.get("at"),o.get("relationship"),o.get("urn"),o.get("organisation"),o.get("source"),o.get("status","NEW")])
def log_run(started,dry,state,actions,notes=""):append("LinkedIn Agent Runs",[started,now(),"growth",dry,actions,len(state.get("relationships",{})),len(state.get("opportunities",[])),notes])
def log_review(review):append("LinkedIn Weekly Reviews",[now(),json.dumps(review,ensure_ascii=False)])
