"""Generate LinkedIn OAuth URL or exchange a returned code locally/CI.
Secrets/tokens are printed only when explicitly exchanging; never commit output.
"""
from __future__ import annotations
import os,secrets,sys,urllib.parse,requests
CLIENT=os.environ.get("LINKEDIN_CLIENT_ID","");SECRET=os.environ.get("LINKEDIN_CLIENT_SECRET","");REDIRECT=os.environ.get("LINKEDIN_REDIRECT_URI","")
SCOPES="openid profile email w_member_social"
def auth_url():
 state=os.environ.get("LINKEDIN_OAUTH_STATE") or secrets.token_urlsafe(24)
 q=urllib.parse.urlencode({"response_type":"code","client_id":CLIENT,"redirect_uri":REDIRECT,"state":state,"scope":SCOPES})
 return "https://www.linkedin.com/oauth/v2/authorization?"+q,state
def exchange(code):
 r=requests.post("https://www.linkedin.com/oauth/v2/accessToken",data={"grant_type":"authorization_code","code":code,"client_id":CLIENT,"client_secret":SECRET,"redirect_uri":REDIRECT},timeout=30);r.raise_for_status();return r.json()
if __name__=="__main__":
 if not CLIENT or not REDIRECT:raise SystemExit("Set LINKEDIN_CLIENT_ID and LINKEDIN_REDIRECT_URI")
 if len(sys.argv)>1 and sys.argv[1]=="exchange":
  if not SECRET or len(sys.argv)<3:raise SystemExit("exchange requires secret and code")
  print(exchange(sys.argv[2]))
 else:
  url,state=auth_url();print("AUTH URL:",url);print("STATE (verify on callback):",state)
