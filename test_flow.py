"""End-to-end tests. Run: DB_PATH=/tmp/t.db python test_flow.py   or   DATABASE_URL=postgresql://... python test_flow.py"""
import os,re,time
os.environ.setdefault("DEV_SHOW_CODES","1"); os.environ.setdefault("SECURE_COOKIES","0")
from fastapi.testclient import TestClient
import app.main as M
from app.dbx import db
KEYS={"PACK-KEY-1":(M.PACK_ID,{"email":"tradie@example.com.au"}),"PACK-KEY-2":(M.PACK_ID,{"email":"tradie@example.com.au"}),"PRO-KEY-1":("dH-NHPOh2YK74-gz4J8DwA==",{"email":"boss@example.com.au"})}
real_verify=M.verify_license
M.verify_license=lambda k:KEYS.get(k.strip())
SAVE=os.environ.get("SAVE_HTML"); R=[]
def ok(n,c): R.append(bool(c)); print("PASS" if c else "FAIL",n)
def save(name,html):
    if SAVE: open(f"{SAVE}/{name}.html","w").write(html)
c=TestClient(M.app); c.get("/")
save("home",c.get("/").text)
f=dict(biz="Smith Painting",site="12 Example St, Brunswick",state="VIC",start="2026-11-09",height="ewp",power="y",old="y",road="n",website="")
r=c.post("/preview",data=f); save("preview",r.text)
ok("A preview: filled, watermarked","Smith Painting" in r.text and 'class="card wm"' in r.text)
ok("A locked risks named from answers","Powerlines near the eaves and gutters — locked" in r.text and "Pre-1990 prep: lead paint &amp; asbestos — locked" in r.text and "EWP rescue plan" in r.text and "Traffic next to" not in r.text)
ok("A primary CTA is per-job $19","Unlock your full SWMS for this job — $19" in r.text)
tok=re.search(r"name=tok value='([^']+)'",r.text).group(1).replace("&quot;",'"')
ok("A disposable email blocked","Temporary" in c.post("/download/start",data=dict(tok=tok,email="x@mailinator.com")).text)
hp=c.post("/preview",data={**f,"website":"spam"}).text; ok("A honeypot drops silently","Thanks" in hp and "Safe Work" not in hp)
r=c.post("/download/start",data=dict(tok=tok,email="tradie@example.com.au")); code=re.search(r"DEV MODE code: (\d{6})",r.text).group(1)
ok("A wrong code rejected","wrong or expired" in c.post("/download/verify",data=dict(email="tradie@example.com.au",code="000000")).text)
r=c.post("/download/verify",data=dict(email="tradie@example.com.au",code=code)); ok("A verified -> download + $19 unlock CTA","Download my free PDF" in r.text and "for this job — $19" in r.text)
u=re.search(r'href="(/download/pdf\?tok=[^"]+)"',r.text).group(1).replace("&quot;",'"').replace("&amp;","&")
p=c.get(u); ok("A watermarked PDF (no locked sections)",p.headers["content-type"]=="application/pdf"); open("sample_free_preview.pdf","wb").write(p.content)
ok("A code can't be reused","wrong or expired" in c.post("/download/verify",data=dict(email="tradie@example.com.au",code=code)).text)
# per-job unlock
r=c.post("/unlock/start",data=dict(tok=tok)); save("unlock",r.text); upath=str(r.url.path)
ok("B unlock page prefilled + Gumroad lldel overlay","12 Example St, Brunswick" in r.text and "labourchef.gumroad.com/l/lldel" in r.text and "gumroad-button" in r.text)
ok("B bogus key rejected","isn't valid" in c.post(upath,data=dict(key="NOPE")).text)
M.verify_license=real_verify; ok("B live Gumroad verify rejects fake key",M.verify_license("FAKE-0000-0000") is None); M.verify_license=lambda k:KEYS.get(k.strip())
r=c.post(upath,data=dict(key="PACK-KEY-1")); save("success",r.text); sid=int(re.search(r"/done/(\d+)",str(r.url)).group(1))
ok("B success: account made, SWMS ready, Unlimited upsell","Your SWMS is ready" in r.text and "tradie@example.com.au" in r.text and "Unlimited — $9/month" in r.text and "l/gztwsf" in r.text)
p=c.get(f"/swms/{sid}/pdf"); ok("B clean PDF of that job",p.headers["content-type"]=="application/pdf"); open("sample_pro.pdf","wb").write(p.content)
d=c.get(f"/swms/{sid}/docx"); ok("B DOCX of that job",d.content[:2]==b"PK"); open("sample_pro.docx","wb").write(d.content)
v=c.get(f"/swms/{sid}").text; ok("B full SWMS has the locked sections","Work near overhead powerlines" in v and "pre-1990" in v and "locked" not in v)
r=c.post(f"/swms/{sid}/sign",data=dict(name="Dave Smith",dt="2026-11-09")); ok("B sign-off saved","Dave Smith" in r.text)
lib=c.get("/app").text; ok("B library shows job + upsell, no unlimited create","Brunswick" in lib and "Unlimited — $9/month" in lib and "/swms/new" not in lib)
ok("B non-Unlimited can't create via /swms/new",c.get("/swms/new",follow_redirects=False).status_code==303)
# reuse of same $19 key for a new job must not create a 2nd SWMS
r2=c.post("/preview",data={**f,"site":"99 Other Rd"}); t2=re.search(r"name=tok value='([^']+)'",r2.text).group(1).replace("&quot;",'"')
up2=str(c.post("/unlock/start",data=dict(tok=t2)).url.path); r=c.post(up2,data=dict(key="PACK-KEY-1"))
ok("B one $19 key = one job (reuse returns original)",f"/done/{sid}" in str(r.url) and "99 Other Rd" not in c.get("/app").text)
up3=str(c.post("/unlock/start",data=dict(tok=t2)).url.path); r=c.post(up3,data=dict(key="PACK-KEY-2"))
ok("B second $19 key unlocks second job","99 Other Rd" in c.get("/app").text)
# re-download later from a fresh device via email code login
c2=TestClient(M.app); ok("B other visitor can't open SWMS","No password" in c2.get(f"/swms/{sid}").text or "/pro" in str(c2.get(f"/swms/{sid}").url))
r=c2.post("/login/start",data=dict(email="tradie@example.com.au")); code=re.search(r"DEV MODE code: (\d{6})",r.text).group(1)
c2.post("/login/verify",data=dict(email="tradie@example.com.au",code=code)); ok("B passwordless re-login -> re-download",c2.get(f"/swms/{sid}/pdf").headers["content-type"]=="application/pdf")
ok("B $19 key can't activate Unlimited","isn't an active Unlimited" in c2.post("/unlock",data=dict(key="PACK-KEY-1")).text)
# Unlimited
c3=TestClient(M.app); r=c3.post("/login/license",data=dict(key="PRO-KEY-1")); ok("C Unlimited key login -> library with New","/swms/new" in c3.get("/app").text)
c3.post("/profile",data=dict(business="Boss Painting Pty Ltd",abn="12 345 678 901",contact="Jo Boss",phone="0400 000 000",crew="Dave, Priya",equipment="Ladders",state="NSW"))
ok("C new SWMS prefilled from profile","Boss Painting Pty Ltd" in c3.get("/swms/new").text)
r=c3.post("/swms/new",data=dict(biz="Boss Painting Pty Ltd",site="4 Road St, Geelong",state="VIC",start="2026-11-20",height="scaffold",power="n",old="n",road="y")); s3=int(re.search(r"/swms/(\d+)/pdf",r.text).group(1))
ok("C tailored (road yes, powerlines no)","Work next to a road" in r.text and "Work near overhead powerlines" not in r.text)
c3.post(f"/swms/{s3}/edit",data=dict(biz="Boss Painting Pty Ltd",site="4 Road St, Geelong",state="VIC",start="2026-11-21",height="ewp",power="n",old="n",road="y")); ok("C edit saved","2026-11-21" in c3.get(f"/swms/{s3}/edit").text)
ok("C duplicate","Create SWMS for new job" in c3.post(f"/swms/{s3}/dup").text)
ok("C no upsell for Unlimited","Unlimited — $9/month" not in c3.get("/app").text)
for i in range(25): r=c.post("/preview",data=f)
ok("A rate limit kicks in","Too many previews" in r.text)
print(sum(R),"/",len(R))
