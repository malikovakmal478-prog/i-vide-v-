# CODE2VIDEO AI — MVP

## Deploy (GitHub + Render)

1. Ushbu papkadagi fayllarni GitHub repo root qismiga yuklang.
2. Render → New → Web Service → GitHub repo tanlang.
3. Render `render.yaml` ni aniqlaydi. Aniqlamasa:
   - Build command: `pip install -r requirements.txt && playwright install --with-deps chromium`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Deploy tugagach, sayt URL manzilini oching.

## Hozir ishlaydigan imkoniyatlar
- HTML/CSS/JavaScript kodini kiritish.
- Brauzerda jonli preview.
- Chromium orqali sahnani render qilish.
- 720p yoki 1080p MP4 eksport.
- 12–30 FPS, 1–20 soniya.

## Hozircha mavjud bo'lmagan imkoniyatlar
Bu birinchi ishlaydigan MVP. Python, C/C++, Java, Go, Rust, Blender/Manim va haqiqiy AI code analysis hali ulanmagan. Bularni keyingi bosqichda alohida workerlar va xavfsiz sandbox arxitekturasi bilan qo'shish kerak.

## Muhim xavfsizlik va hosting cheklovlari
- Bu MVP faqat o'zingiz ishonadigan HTML/JS kod bilan sinash uchun. Uni ommaga ochiq, ko'p foydalanuvchili servis sifatida ishga tushirishdan oldin render workerini alohida izolyatsiya qilish, autentifikatsiya, rate limit, fayl muddati va resurs limitlari qo'shilishi shart.
- Render Free xizmatida render jarayoni sekin bo'lishi yoki servis uyquga ketishi mumkin. 4K, uzoq video va parallel renderlar hozircha yo'q.
- Vaqtinchalik video fayllar server diskida saqlanadi; bepul servis qayta ishga tushganda yo'qolishi mumkin.
