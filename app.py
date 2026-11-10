import os, re, uuid, shutil, threading, subprocess, asyncio
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"outputs"; UP=ROOT/"uploads"
OUT.mkdir(exist_ok=True); UP.mkdir(exist_ok=True)
app=Flask(__name__); app.config["MAX_CONTENT_LENGTH"]=20*1024*1024
JOBS={}; LOCK=threading.Lock()
SIZES={"youtube":(1920,1080),"tiktok":(1080,1920),"shorts":(1080,1920),"reels":(1080,1920),"square":(1080,1080)}

PAGE=r"""<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CODE2VIDEO AI</title><style>
*{box-sizing:border-box}body{margin:0;background:#080b14;color:#edf0ff;font:15px Inter,system-ui,Arial}nav{height:66px;padding:0 5%;display:flex;align-items:center;justify-content:space-between;background:#0c1120;border-bottom:1px solid #252d45}nav b{letter-spacing:1px}nav i,h1 em{color:#a894ff;font-style:normal}nav span,small{color:#8793b3;font-size:11px;letter-spacing:2px}main{max-width:1160px;margin:auto;padding:38px 20px}header{text-align:center;margin-bottom:30px}h1{font-size:clamp(34px,5vw,55px);margin:13px 0}header p{color:#9ba7c5}.studio{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.panel{background:#111827;border:1px solid #28314b;border-radius:17px;padding:21px;box-shadow:0 18px 50px #0004}.tabs{display:flex;gap:7px;margin-bottom:18px}.tab{background:#1a2237;color:#b6bfd7;border:1px solid #303b5a;border-radius:9px;padding:10px;cursor:pointer}.tab.active{background:#352963;color:white;border-color:#8068e8}label{display:block;color:#cbd3e8;font-size:12px;margin:14px 0 7px}textarea,select,input[type=file]{width:100%;background:#090e1a;color:#eaf0ff;border:1px solid #303b56;border-radius:9px;padding:12px;font:13px ui-monospace,monospace}textarea{min-height:220px;resize:vertical;line-height:1.5}.hint{font-size:11px;color:#8290ae;line-height:1.5}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.create{width:100%;padding:15px;border:0;border-radius:10px;margin-top:18px;background:linear-gradient(100deg,#785cff,#248fd7);color:white;font-weight:800;cursor:pointer}.create:disabled{opacity:.5}.preview{display:flex;flex-direction:column}.top{display:flex;justify-content:space-between;color:#99a5c1;font-size:10px;letter-spacing:1px}.top b{color:#69d9a1}.screen{flex:1;min-height:330px;margin:18px 0;border:1px solid #293451;border-radius:12px;background:radial-gradient(circle at 50% 40%,#292354,#0a1020 70%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:25px}.play{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;background:#392d6c;color:#c5b9ff}.screen p{font-size:12px;color:#8794b4;max-width:260px}#status{font-size:12px;color:#b4bfd8;margin-bottom:9px}.progress{height:6px;background:#29324a;border-radius:8px;overflow:hidden}.progress div{height:100%;width:0;background:linear-gradient(90deg,#886aff,#4bc8ef);transition:width .3s}#download{display:block;text-align:center;margin-top:14px;padding:12px;border:1px solid #6858a8;border-radius:9px;color:#d2c9ff;text-decoration:none}footer{display:flex;justify-content:space-between;color:#75819f;font-size:11px;padding:25px 4px}@media(max-width:800px){.studio{grid-template-columns:1fr}main{padding:25px 13px}.screen{min-height:210px}nav span{display:none}footer{flex-direction:column;gap:8px}}
</style></head><body><nav><b>◈ CODE2VIDEO <i>AI</i></b><span>CREATIVE VIDEO STUDIO</span></nav><main><header><small>✦ AI VIDEO WORKSPACE</small><h1>G‘oyangizni <em>videoga</em> aylantiring.</h1><p>HTML, hikoya yoki rasmdan MP4 yarating.</p></header><div class="studio"><section class="panel"><div class="tabs"><button class="tab active" data-mode="code">Code → Video</button><button class="tab" data-mode="story">Story → Video</button><button class="tab" data-mode="image">Image → Video</button></div><form id="form"><input type="hidden" name="mode" id="mode" value="code"><div id="codeBox"><label>HTML / CSS / JavaScript</label><textarea name="html" spellcheck="false"><!doctype html><html><head><style>body{margin:0;height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#10152e,#39216b);font:bold 60px Arial;color:white}h1{animation:float 2s infinite alternate}@keyframes float{to{transform:translateY(-35px);color:#9d8cff}}</style></head><body><h1>Hello, world!</h1></body></html></textarea><p class="hint">HTML/CSS/JS Chromium'da kadrma-kadr yoziladi.</p></div><div id="storyBox" hidden><label>Hikoya (bo‘sh qator — yangi sahna)</label><textarea name="story" placeholder="Hikoyangizni yozing..."></textarea><p class="hint">Hikoya animatsion matnli sahnalarga aylanadi; generativ AI rasm emas.</p></div><div id="imageBox" hidden><label>Rasm yuklash</label><input type="file" name="image" accept="image/png,image/jpeg,image/webp"><p class="hint">Rasmga zoom/pan kamera harakati beriladi; bu generativ AI video emas.</p></div><div class="grid"><div><label>Format</label><select name="format"><option value="youtube">YouTube · 16:9</option><option value="tiktok">TikTok · 9:16</option><option value="shorts">Shorts · 9:16</option><option value="reels">Reels · 9:16</option><option value="square">Instagram · 1:1</option></select></div><div><label>Davomiylik</label><select name="duration"><option>5</option><option selected>8</option><option>12</option><option>15</option><option>20</option><option>30</option></select></div></div><label>Ovozli matn (ixtiyoriy)</label><textarea name="voice_text" rows="2" style="min-height:65px" placeholder="Ovozga aylantiriladigan matn..."></textarea><select name="voice"><option value="uz-UZ-MadinaNeural">O‘zbekcha ayol — Madina</option><option value="uz-UZ-SardorNeural">O‘zbekcha erkak — Sardor</option></select><p class="hint">Edge TTS internetga bog‘liq. Ovoz mavjud bo‘lsa MP4 ichiga qo‘shiladi.</p><button class="create" id="create">✦ Video yaratish</button></form></section><section class="panel preview"><div class="top">LIVE WORKSPACE <b>● READY</b></div><div class="screen"><div class="play">▶</div><h3>Your canvas</h3><p>Render tugagach MP4 yuklab olish havolasi chiqadi.</p></div><div id="status">Hozircha render yo‘q.</div><div class="progress"><div id="bar"></div></div><a id="download" hidden>↓ MP4 yuklab olish</a></section></div><footer>CODE2VIDEO AI <span>Flask · Chromium · FFmpeg · Edge TTS</span></footer></main><script>
const tabs=[...document.querySelectorAll('.tab')],mode=document.querySelector('#mode'),boxes={code:document.querySelector('#codeBox'),story:document.querySelector('#storyBox'),image:document.querySelector('#imageBox')};tabs.forEach(t=>t.onclick=()=>{tabs.forEach(x=>x.classList.toggle('active',x===t));mode.value=t.dataset.mode;Object.entries(boxes).forEach(([k,v])=>v.hidden=k!==mode.value)});const form=document.querySelector('#form'),btn=document.querySelector('#create'),st=document.querySelector('#status'),bar=document.querySelector('#bar'),link=document.querySelector('#download');form.onsubmit=async e=>{e.preventDefault();btn.disabled=true;link.hidden=true;st.textContent='Render boshlanmoqda...';bar.style.width='0%';try{let r=await fetch('/api/create',{method:'POST',body:new FormData(form)}),created=await r.json();if(!r.ok)throw Error(created.error||'So‘rov xatosi');const jobId=created.id;if(!jobId)throw Error('Server vazifa ID raqamini qaytarmadi');let finished=false;for(let n=0;n<900;n++){r=await fetch('/api/status/'+encodeURIComponent(jobId),{cache:'no-store'});let j=await r.json();if(!r.ok)throw Error(j.error||'Vazifa holatini olishda xatolik');bar.style.width=(j.progress||0)+'%';st.textContent=j.message||j.status||'Render davom etmoqda';if(j.status==='done'){if(!j.url)throw Error('Video tayyor, lekin yuklab olish manzili kelmadi');link.href=j.url;link.hidden=false;st.textContent='Video tayyor!';finished=true;break}if(j.status==='error')throw Error(j.message||'Video yaratishda xatolik');await new Promise(ok=>setTimeout(ok,1500))}if(!finished)throw Error('Render vaqti tugadi')}catch(err){st.textContent='Xatolik: '+err.message}finally{btn.disabled=false}};
</script></body></html>"""

def run(c,timeout=900):
 p=subprocess.run(c,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
 if p.returncode: raise RuntimeError(p.stderr.decode("utf8","replace")[-2200:])
def ffmpeg():
 x=shutil.which("ffmpeg")
 if not x: raise RuntimeError("FFmpeg topilmadi. Render build logini tekshiring.")
 return x
def update(i,**v):
 with LOCK: JOBS[i].update(v)
def make_tts(text,voice,path):
 import edge_tts
 async def go(): await edge_tts.Communicate(text,voice).save(str(path))
 asyncio.run(go()); return path
def capture(html,w,h,d,folder):
 from playwright.sync_api import sync_playwright
 folder.mkdir(parents=True,exist_ok=True); pagefile=folder/"scene.html"; pagefile.write_text(html,encoding="utf8")
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
  page=browser.new_page(viewport={"width":w,"height":h})
  page.goto(pagefile.as_uri(),wait_until="load",timeout=30000); page.wait_for_timeout(350)
  for n in range(d*24):
   page.screenshot(path=str(folder/f"frame_{n:06}.png")); page.wait_for_timeout(42)
  browser.close()
 return folder/"frame_%06d.png"
def encode(pattern,dest,w,h,audio=None):
 c=[ffmpeg(),"-y","-framerate","24","-i",str(pattern)]
 if audio:c+=["-i",str(audio)]
 c+=["-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,format=yuv420p","-c:v","libx264","-preset","ultrafast","-crf","23"]
 if audio:c+=["-map","0:v:0","-map","1:a:0","-c:a","aac","-b:a","128k","-shortest"]
 else:c+=["-an"]
 c+=["-movflags","+faststart",str(dest)];run(c)
def render(i,x):
 work=ROOT/"work"/i;work.mkdir(parents=True,exist_ok=True)
 try:
  w,h=SIZES[x["format"]];audio=None;dest=OUT/(i+".mp4")
  update(i,status="running",progress=5,message="Render tayyorlanmoqda")
  if x["voice_text"]:
   update(i,progress=10,message="Ovoz yaratilmoqda");audio=make_tts(x["voice_text"],x["voice"],work/"voice.mp3")
  if x["mode"]=="image":
   update(i,progress=25,message="Rasmga kamera harakati berilmoqda")
   vf=f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},zoompan=z='min(zoom+0.0008,1.18)':d={x['duration']*24}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=24,format=yuv420p"
   c=[ffmpeg(),"-y","-loop","1","-i",x["image"],"-t",str(x["duration"]),"-vf",vf,"-c:v","libx264","-preset","ultrafast","-crf","23"]
   if audio:c+=["-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:a","aac","-shortest"]
   else:c+=["-an"]
   c+=["-movflags","+faststart",str(dest)];run(c)
  else:
   html=x["html"]
   if x["mode"]=="story":
    scenes=[s.strip() for s in re.split(r"\n\s*\n",x["story"]) if s.strip()] or ["Hikoya"]
    cards="".join('<section><small>SCENE %02d</small><h1>%s</h1></section>'%(n+1,s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")) for n,s in enumerate(scenes))
    html='<!doctype html><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;background:#090d1c;color:white;font:bold 5vw Arial}section{height:100vh;padding:9%;display:flex;flex-direction:column;justify-content:center;background:radial-gradient(circle at 80% 20%,#39276c,#10172f 65%)}section:nth-child(even){background:radial-gradient(circle,#15506c,#10172f)}small{font-size:14px;color:#a999ff;letter-spacing:5px}h1{animation:up 1s both}@keyframes up{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}</style>'+cards
   update(i,progress=25,message="Chromium kadrlarni yozmoqda")
   pattern=capture(html,w,h,x["duration"],work/"frames")
   update(i,progress=80,message="MP4 kodlanmoqda");encode(pattern,dest,w,h,audio)
  update(i,status="done",progress=100,message="Video tayyor",url="/video/"+i+".mp4")
 except Exception as e:update(i,status="error",progress=100,message=str(e))
 finally:shutil.rmtree(work,ignore_errors=True)
@app.get("/")
def home():return Response(PAGE,mimetype="text/html")
@app.get("/health")
def health():return jsonify(status="ok")
@app.post("/api/create")
def create():
 mode=request.form.get("mode","code");fmt=request.form.get("format","youtube")
 if fmt not in SIZES:return jsonify(error="Format noto‘g‘ri"),400
 try:d=max(2,min(30,int(request.form.get("duration",8))))
 except:d=8
 x={"mode":mode,"format":fmt,"duration":d,"voice_text":request.form.get("voice_text","").strip(),"voice":request.form.get("voice","uz-UZ-MadinaNeural")}
 if mode=="image":
  f=request.files.get("image")
  if not f or not f.filename:return jsonify(error="Rasm yuklang"),400
  ext=Path(secure_filename(f.filename)).suffix.lower()
  if ext not in (".png",".jpg",".jpeg",".webp"):return jsonify(error="PNG/JPG/WEBP rasm kerak"),400
  p=UP/(uuid.uuid4().hex+ext);f.save(p);x["image"]=str(p)
 elif mode=="story":
  x["story"]=request.form.get("story","").strip()
  if not x["story"]:return jsonify(error="Hikoya matnini kiriting"),400
 else:
  x["html"]=request.form.get("html","").strip()
  if not x["html"]:return jsonify(error="HTML kod kiriting"),400
 i=uuid.uuid4().hex[:12]
 with LOCK:JOBS[i]={"status":"queued","progress":0,"message":"Navbatda"}
 threading.Thread(target=render,args=(i,x),daemon=True).start()
 return jsonify(id=i),202
@app.get("/api/status/<i>")
def status(i):
 with LOCK:j=JOBS.get(i)
 return (jsonify(j),200) if j else (jsonify(error="Topilmadi"),404)
@app.get("/video/<name>")
def video(name):
 if not re.fullmatch(r"[a-f0-9]{12}\.mp4",name):return "Not found",404
 p=OUT/name
 if not p.exists():return "Not found",404
 return send_file(p,as_attachment=True,download_name="code2video.mp4")
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
