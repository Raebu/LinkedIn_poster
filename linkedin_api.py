"""Small official LinkedIn REST client. No scraping or unofficial endpoints."""
from __future__ import annotations
import os, requests

API="https://api.linkedin.com"
VERSION=os.getenv("LINKEDIN_VERSION","202609")

class LinkedIn:
 def __init__(self,token=None):
  self.token=token or os.environ["LINKEDIN_ACCESS_TOKEN"]
  self.h={"Authorization":f"Bearer {self.token}","X-Restli-Protocol-Version":"2.0.0","Linkedin-Version":VERSION,"Content-Type":"application/json"}
 def _request(self,method,path,**kw):
  r=requests.request(method,API+path,headers=self.h,timeout=30,**kw)
  if not r.ok: raise RuntimeError(f"LinkedIn {r.status_code}: {r.text[:800]}")
  return r
 def userinfo(self):
  r=requests.get(API+"/v2/userinfo",headers={"Authorization":f"Bearer {self.token}"},timeout=30);r.raise_for_status();return r.json()
 def person_urn(self):
  sub=self.userinfo()["sub"];return f"urn:li:person:{sub}"
 def create_post(self,text,author=None,visibility="PUBLIC"):
  body={"author":author or self.person_urn(),"commentary":text,"visibility":visibility,"distribution":{"feedDistribution":"MAIN_FEED","targetEntities":[],"thirdPartyDistributionChannels":[]},"lifecycleState":"PUBLISHED","isReshareDisabledByAuthor":False}
  r=self._request("POST","/rest/posts",json=body);return r.headers.get("x-restli-id","")
 def reshare(self,parent_urn,commentary="",author=None):
  body={"author":author or self.person_urn(),"commentary":commentary,"visibility":"PUBLIC","distribution":{"feedDistribution":"MAIN_FEED","targetEntities":[],"thirdPartyDistributionChannels":[]},"lifecycleState":"PUBLISHED","isReshareDisabledByAuthor":False,"reshareContext":{"parent":parent_urn}}
  r=self._request("POST","/rest/posts",json=body);return r.headers.get("x-restli-id","")
