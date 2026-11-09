
import os
import re
import uuid
import shutil
import asyncio
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import imageio_ffmpeg
from playwright.async_api import async_playwright

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/tmp/code2video_outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CODE2VIDEO AI", version="0.1.0")

PAGE = r"""<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CODE2VIDEO AI Studio</title>
<style>
:root{--bg:#080b14;--panel:#111827;--line:#253149;--muted:#91a0b9;--text:#eef3ff;--a:#7c5cff;--b:#22d3ee}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0%,#1b2450 0,transparent 35%),radial-gradient(circle at 90% 15%,#123b4c 0,transparent 28%),var(--bg);color:var(--text);font:15px Inter,system-ui,Arial}
header{height:72px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 4vw;background:#090e1bd9;position:sticky;top:0;z-index:2;backdrop-filter:blur(12px)}
.brand{font-weight:900;letter-spacing:1.5px;font-size:19px}.brand span{color:#9a87ff}.status{color:#a9b7ce;font-size:12px}
main{max-width:1440px;margin:auto;padding:28px 22px}.hero{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}.hero h1{font-size:clamp(27px,4vw,42px);margin:0 0 8px}.hero p{color:var(--muted);margin:0;max-width:720px;line-height:1.55}
.layout{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,1fr);gap:18px}.panel{background:linear-gradient(145deg,#141d30,#0e1524);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 18px 60px #0003;min-width:0}.panel h2{font-size:16px;margin:0 0 14px}.toolbar{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:12px}select,input,textarea{background:#080f1d;border:1px solid #2b3851;color:var(--text);border-radius:10px;padding:10px;font:inherit}select{min-width:145px}textarea{width:100%;min-height:390px;resize:vertical;line-height:1.55;font:13px ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:2}
button{border:0;border-radius:11px;padding:11px 16px;font-weight:750;cursor:pointer;color:white;background:linear-gradient(100deg,var(--a),#4c8dff);transition:.2s}button:hover{filter:brightness(1.13);transform:translateY(-1px)}button.secondary{background:#202c42;border:1px solid #35435d}button:disabled{opacity:.55;cursor:wait;transform:none}
.preview{width:100%;aspect-ratio:16/9;border:1px solid #34415a;border-radius:12px;background:#050810;overflow:hidden}.preview iframe{width:100%;height:100%;border:0;background:white}.settings{display:flex;gap:10px;flex-wrap:wrap;margin:13px 0}.settings label{display:flex;flex-direction:column;gap:6px;color:var(--muted);font-size:12px}.settings input{width:110px}.hint,.message{color:var(--muted);font-size:12px;line-height:1.55}.message{margin-top:12px;min-height:20px}.download{display:none;margin-top:14px}.examples{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.examples button{font-size:12px;padding:8px 10px}
footer{color:#71809a;text-align:center;font-size:12px;padding:24px}
@media(max-width:850px){.layout{grid-template-columns:1fr}.hero{display:block}.status{display:none}textarea{min-height:300px}}
</style></head>
<body>
<header><div class="brand">CODE<span>2</span>VIDEO <span>AI</span></div><div class="status">CODE-TO-VIDEO STUDIO · BETA</div></header>
<main>
<section class="hero"><div><h1>Kodingizni videoga aylantiring.</h1><p>HTML, CSS va JavaScript animatsiyalarini brauzerda ishga tushiring va MP4 video sifatida render qiling. Keyingi versiyalarda Python/3D va boshqa tillar uchun alohida workerlar ulanadi.</p></div></section>
<div class="layout">
<section class="panel"><h2>01 · Kod muharriri</h2>
<div class="toolbar"><select id="language"><option value="html">HTML + CSS + JavaScript</option><option value="javascript">JavaScript (HTML ichida)</option></select><button class="secondary" id="sample">Namuna kod</button><button class="secondary" id="clear">Tozalash</button></div>
<textarea id="code" spellcheck="false" placeholder="HTML/CSS/JavaScript kodingizni shu yerga joylang..."></textarea>
<div class="settings">
<label>Video davomiyligi (soniya)<input id="duration" type="number" min="1" max="20" value="5"></label>
<label>FPS<input id="fps" type="number" min="12" max="30" value="24"></label>
<label>O‘lcham<select id="resolution"><option value="1280x720">720p</option><option value="1920x1080" selected>1080p</option></select></label>
</div>
<button id="previewBtn" class="secondary">▶ Ko‘rib chiqish</button> <button id="renderBtn">🎬 MP4 yaratish</button>
<div class="message" id="message">Kod kiriting va avval ko‘rib chiqing.</div>
</section>
<section class="panel"><h2>02 · Jonli ko‘rinish</h2><div class="preview"><iframe id="preview" sandbox="allow-scripts"></iframe></div>
<p class="hint">Eslatma: render paytida kod alohida Chromium sahifasida bajariladi. Video — sahnaning vaqt bo‘yicha olingan kadrlaridan tuziladi.</p>
<a class="download" id="download" href="#" download="code2video.mp4"><button>⬇ MP4 videoni yuklab olish</button></a>
</section></div>
</main><footer>CODE2VIDEO AI · Early MVP · Faqat o‘zingiz ishonadigan kodni kiriting.</footer>
<script>
const $=id=>document.getElementById(id);
const sample=`<!doctype html>
<html><head><style>
*{box-sizing:border-box}body{margin:0;height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#10152e,#182e4b);font-family:Arial;color:white;overflow:hidden}
.scene{text-align:center}.orb{width:130px;height:130px;margin:auto;border-radius:50%;background:radial-gradient(circle at 30% 25%,#fff,#54d8ff 18%,#765cff 55%,#161c55);box-shadow:0 0 65px #5d8dff;animation:float 2s ease-in-out infinite alternate}
h1{font-size:42px;margin:28px 0 8px;letter-spacing:2px}p{color:#b9c9ee}
@keyframes float{to{transform:translateY(-35px) rotate(18deg);filter:hue-rotate(35deg)}}
</style></head><body><div class="scene"><div class="orb"></div><h1>HELLO, WORLD</h1><p>CODE → VIDEO</p></div></body></html>`;
function makeDoc(){let c=$('code').value; if($('language').value==='javascript')return `<!doctype html><html><body style="margin:0"><script>${c.replace(/<\/script/gi,'<\\/script')}<\/script></body></html>`;return c}
$('sample').onclick=()=>{$('language').value='html';$('code').value=sample;preview()};
$('clear').onclick=()=>{$('code').value='';$('preview').srcdoc='';$('download').style.display='none'};
function preview(){if(!$('code').value.trim()){msg('Avval kod kiriting.');return} $('preview').srcdoc=makeDoc();msg('Ko‘rib chiqish yangilandi.')};
$('previewBtn').onclick=preview;
function msg(t){$('message').textContent=t}
$('renderBtn').onclick=async()=>{
 const code=$('code').value.trim();if(!code){msg('Avval kod kiriting.');return}
 const duration=Number($('duration').value),fps=Number($('fps').value);
 if(!Number.isFinite(duration)||duration<1||duration>20){msg('Davomiylik 1–20 soniya oralig‘ida bo‘lsin.');return}
 if(!Number.isFinite(fps)||fps<12||fps>30){msg('FPS 12–30 oralig‘ida bo‘lsin.');return}
 $('renderBtn').disabled=true;$('download').style.display='none';msg('Video render qilinmoqda. Bu bir necha daqiqa olishi mumkin...');
 try{
  const r=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,language:$('language').value,duration,fps,resolution:$('resolution').value})});
  const data=await r.json();if(!r.ok)throw new Error(data.detail||'Render xatosi');
  $('download').href=data.download_url;$('download').style.display='inline-block';msg('Tayyor! MP4 video yaratildi.');
 }catch(e){msg('Xatolik: '+e.message)}finally{$('renderBtn').disabled=false}
};
</script></body></html>"""

class RenderRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200000)
    language: str = "html"
    duration: int = Field(default=5, ge=1, le=20)
    fps: int = Field(default=24, ge=12, le=30)
    resolution: str = "1920x1080"

@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE

@app.get("/health")
async def health():
    return {"status": "ok", "app": "CODE2VIDEO AI"}

@app.post("/api/render")
async def render_video(req: RenderRequest):
    if req.language not in ("html", "javascript"):
        raise HTTPException(400, "Bu versiyada HTML/JavaScript renderi mavjud.")
    if req.resolution not in ("1280x720", "1920x1080"):
        raise HTTPException(400, "Ruxsat etilgan formatlar: 720p yoki 1080p.")
    if re.search(r"<\s*iframe|<\s*object|<\s*embed", req.code, re.I):
        raise HTTPException(400, "iframe/object/embed elementlari hozircha bloklangan.")
    width, height = map(int, req.resolution.split("x"))
    job_id = uuid.uuid4().hex
    out_file = OUTPUT_DIR / f"{job_id}.mp4"
    work_dir = Path(tempfile.mkdtemp(prefix="c2v_"))
    frame_file = work_dir / "frame.png"
    html = req.code if req.language == "html" else (
        "<!doctype html><html><body style='margin:0'><script>" +
        req.code.replace("</script", "<\\/script") +
        "</script></body></html>"
    )
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    writer = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            # Block all outbound requests from user-supplied page code.
            await context.route("**/*", lambda route: route.abort())
            page = await context.new_page()
            await page.set_content(html, wait_until="load", timeout=15000)
            await page.wait_for_timeout(500)
            writer = imageio_ffmpeg.write_frames(
                str(out_file), (width, height), fps=req.fps,
                codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
                macro_block_size=1, ffmpeg_log_level="error"
            )
            writer.send(None)
            import numpy as np
            from PIL import Image
            total = req.duration * req.fps
            for i in range(total):
                await page.screenshot(path=str(frame_file), type="png")
                frame = np.asarray(Image.open(frame_file).convert("RGB"))
                writer.send(frame)
                await page.wait_for_timeout(max(1, round(1000 / req.fps)))
            writer.close()
            writer = None
            await browser.close()
        if not out_file.exists() or out_file.stat().st_size < 1000:
            raise RuntimeError("Video fayli yaratilmadi.")
        return {"ok": True, "download_url": f"/api/download/{job_id}", "size_bytes": out_file.stat().st_size}
    except Exception as e:
        if writer:
            try: writer.close()
            except: pass
        if out_file.exists(): out_file.unlink()
        raise HTTPException(500, f"Render bajarilmadi: {str(e)[:500]}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    if not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise HTTPException(404, "Video topilmadi.")
    path = OUTPUT_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(404, "Video topilmadi yoki vaqtinchalik saqlash muddati tugagan.")
    return FileResponse(path, media_type="video/mp4", filename="code2video.mp4")
