"""Deterministic, dependency-light renderers for useful LinkedIn visuals and documents."""
from __future__ import annotations
from io import BytesIO
import re,textwrap
from PIL import Image,ImageDraw,ImageFont
from reportlab.lib.pagesizes import landscape,A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _font(size,bold=False):
 for p in (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]):
  try:return ImageFont.truetype(p,size)
  except OSError:pass
 return ImageFont.load_default()

def _clean(s):return re.sub(r"\s+"," ",str(s)).strip()
def _wrap(s,width):return textwrap.wrap(_clean(s),width=width,break_long_words=False) or [""]

def render_visual(brief,topic):
 """Create a clean information card from the generated visual brief; no decorative AI imagery."""
 W,H=1200,1200;im=Image.new("RGB",(W,H),(247,247,245));d=ImageDraw.Draw(im)
 title=_clean(topic)[:100];brief=_clean(brief)
 d.text((80,70),"MARTIN RAEBURN",font=_font(26,True),fill=(35,35,35))
 y=145
 for line in _wrap(title,28)[:3]:d.text((80,y),line,font=_font(54,True),fill=(15,15,15));y+=66
 y+=25;d.line((80,y,1120,y),fill=(80,80,80),width=2);y+=55
 # Turn clauses/steps into a readable sequence of cards.
 parts=[_clean(x) for x in re.split(r"(?:\s*[→>]\s*|[.;]\s+|\n+)",brief) if len(_clean(x))>8][:6]
 if not parts:parts=[brief]
 box_h=max(105,min(150,(900-y)//max(1,len(parts))))
 for i,p in enumerate(parts,1):
  d.rounded_rectangle((80,y,1120,y+box_h),radius=18,outline=(90,90,90),width=2,fill=(255,255,255))
  d.text((105,y+24),str(i),font=_font(28,True),fill=(25,25,25))
  ty=y+20
  for line in _wrap(p,62)[:3]:d.text((165,ty),line,font=_font(28),fill=(30,30,30));ty+=37
  y+=box_h+20
 d.text((80,1130),"Complex thinking. Simple language.",font=_font(22),fill=(75,75,75))
 out=BytesIO();im.save(out,"PNG",optimize=True);return out.getvalue(),f"Diagram explaining {title}"

def render_document(outline,topic):
 """Create a landscape PDF carousel from 5-8 concise page concepts."""
 out=BytesIO();size=landscape(A4);c=canvas.Canvas(out,pagesize=size);W,H=size
 pages=[str(x) for x in outline][:8]
 for n,item in enumerate(pages,1):
  c.setFont("Helvetica-Bold",11);c.drawString(18*mm,H-17*mm,"MARTIN RAEBURN")
  c.setFont("Helvetica",9);c.drawRightString(W-18*mm,H-17*mm,f"{n}/{len(pages)}")
  c.setLineWidth(0.6);c.line(18*mm,H-22*mm,W-18*mm,H-22*mm)
  if n==1:
   heading=_clean(topic)
   body=_clean(item)
  else:
   bits=re.split(r"[:—-]",_clean(item),maxsplit=1);heading=bits[0];body=bits[1] if len(bits)>1 else item
  c.setFont("Helvetica-Bold",25)
  y=H-48*mm
  for line in textwrap.wrap(heading,width=38)[:3]:c.drawString(18*mm,y,line);y-=11*mm
  y-=5*mm;c.setFont("Helvetica",15)
  for line in textwrap.wrap(_clean(body),width=75)[:9]:c.drawString(18*mm,y,line);y-=8*mm
  c.setFont("Helvetica",9);c.drawString(18*mm,12*mm,"Martin Raeburn | Technology, systems and commercial execution")
  c.showPage()
 c.save();return out.getvalue()
