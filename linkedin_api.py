"""Official LinkedIn REST client for publishing and Community Management.

No scraping or unofficial endpoints. Growth credentials are kept separate from the
publisher so Community Management can be enabled without disturbing live posting.
"""
from __future__ import annotations
import os, requests
from urllib.parse import quote

API="https://api.linkedin.com"
VERSION=os.getenv("LINKEDIN_VERSION","202609")

class LinkedIn:
 def __init__(self,token=None):
  self.token=token or os.environ["LINKEDIN_ACCESS_TOKEN"]
  self.h={"Authorization":f"Bearer {self.token}","X-Restli-Protocol-Version":"2.0.0","Linkedin-Version":VERSION,"Content-Type":"application/json"}
 def _request(self,method,path,**kw):
  r=requests.request(method,API+path,headers=self.h,timeout=60,**kw)
  if not r.ok: raise RuntimeError(f"LinkedIn {r.status_code}: {r.text[:800]}")
  return r
 def userinfo(self):
  r=requests.get(API+"/v2/userinfo",headers={"Authorization":f"Bearer {self.token}"},timeout=30);r.raise_for_status();return r.json()
 def person_urn(self):
  sub=self.userinfo()["sub"];return f"urn:li:person:{sub}"
 def _post_body(self,text,author=None,visibility="PUBLIC"):
  return {"author":author or self.person_urn(),"commentary":text,"visibility":visibility,"distribution":{"feedDistribution":"MAIN_FEED","targetEntities":[],"thirdPartyDistributionChannels":[]},"lifecycleState":"PUBLISHED","isReshareDisabledByAuthor":False}
 def create_post(self,text,author=None,visibility="PUBLIC"):
  r=self._request("POST","/rest/posts",json=self._post_body(text,author,visibility));return r.headers.get("x-restli-id","")
 def get_post(self,urn):
  return self._request("GET",f"/rest/posts/{quote(urn,safe='')}?viewContext=READER").json()
 def _initialize_upload(self,kind,owner=None):
  owner=owner or self.person_urn();plural="images" if kind=="image" else "documents"
  r=self._request("POST",f"/rest/{plural}?action=initializeUpload",json={"initializeUploadRequest":{"owner":owner}})
  value=r.json()["value"];return value["uploadUrl"],value[kind]
 def _upload_bytes(self,url,data,content_type):
  r=requests.put(url,data=data,headers={"Authorization":f"Bearer {self.token}","Content-Type":content_type},timeout=120)
  if not r.ok:raise RuntimeError(f"LinkedIn media upload {r.status_code}: {r.text[:500]}")
 def upload_image(self,data,content_type="image/png",owner=None):
  url,urn=self._initialize_upload("image",owner);self._upload_bytes(url,data,content_type);return urn
 def upload_document(self,data,content_type="application/pdf",owner=None):
  url,urn=self._initialize_upload("document",owner);self._upload_bytes(url,data,content_type);return urn
 def create_image_post(self,text,image_bytes,alt_text="",content_type="image/png",author=None,visibility="PUBLIC"):
  author=author or self.person_urn();urn=self.upload_image(image_bytes,content_type,author);body=self._post_body(text,author,visibility);body["content"]={"media":{"id":urn,"altText":alt_text[:4086]}}
  r=self._request("POST","/rest/posts",json=body);return r.headers.get("x-restli-id",""),urn
 def create_document_post(self,text,document_bytes,title="Martin Raeburn — Insight.pdf",author=None,visibility="PUBLIC"):
  author=author or self.person_urn();urn=self.upload_document(document_bytes,"application/pdf",author);body=self._post_body(text,author,visibility);body["content"]={"media":{"id":urn,"title":title}}
  r=self._request("POST","/rest/posts",json=body);return r.headers.get("x-restli-id",""),urn
 def reshare(self,parent_urn,commentary="",author=None):
  body=self._post_body(commentary,author);body["reshareContext"]={"parent":parent_urn}
  r=self._request("POST","/rest/posts",json=body);return r.headers.get("x-restli-id","")
 def create_comment(self,target_urn,text,actor=None):
  """Community Management Comments API; requires w_member_social_feed for member actions."""
  actor=actor or self.person_urn()
  body={"actor":actor,"message":{"text":text},"object":target_urn}
  r=self._request("POST",f"/rest/socialActions/{quote(target_urn,safe='')}/comments",json=body)
  return r.headers.get("x-restli-id","") or r.json().get("id","")
 def create_reaction(self,target_urn,reaction_type="LIKE",actor=None):
  """Community Management Reactions API; requires w_member_social_feed for member actions."""
  actor=actor or self.person_urn()
  body={"root":target_urn,"reactionType":reaction_type}
  r=self._request("POST",f"/rest/reactions?actor={quote(actor,safe='')}",json=body)
  return r.headers.get("x-restli-id","")

def growth_client():
 """Use the dedicated Community Management token when present."""
 token=os.getenv("LINKEDIN_GROWTH_ACCESS_TOKEN") or os.getenv("LINKEDIN_ACCESS_TOKEN")
 return LinkedIn(token)
