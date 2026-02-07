# Loyihani Alohida Serverlarga Joylash Bo'yicha Qo'llanma

Sizning so'rovingiz bo'yicha loyihani 3 qismga bo'lishga tayyorladik:
1. **Frontend + Backend (Web Server)**: Asosiy sayt va API.
2. **Telegram Bot (Bot Server)**: Telegram bilan ishlovchi alohida jarayon.
3. **Database (Ma'lumotlar Bazasi)**: *Qiyin qism (pastda o'qing).*

## 1. Web Server (Frontend va Backend)
Ushbu loyiha **Flask (Python)** da yozilgan bo'lib, Frontend (`templates` html fayllar) va Backend (`app.py` mantiq) birgalikda ishlaydi. Ularni ajratish uchun butun kodni qayta yozish kerak (masalan, Frontendni React ga). Shuning uchun eng to'g'ri yo'l - ularni bitta "Web Server" da qoldirishdir.

**Ishga tushirish:**
Bu serverda faqat sayt va API ishlashi kerak. Botni o'chirib qo'yamiz.
Yangi tayyorlangan skriptdan foydalaning:

```bash
python run_web.py
```

*Bu skript `START_TELEGRAM_BOT=0` sozlamsini qo'llab, botni start bo'lishini oldini oladi.*

## 2. Telegram Bot Serveri
Botni alohida serverga (yoki VPS ga) qo'yishingiz mumkin. U API orqali Web Serverga ulanadi.

**Ishga tushirish:**
1. `.env` faylida yoki server environmentida Web Server manzilini ko'rsating:
   ```
   FLASK_APP_URL=http://<web-server-ip>:5000
   ```
   *(Masalan, agar Web Server IP si 192.168.1.5 bo'lsa: `http://192.168.1.5:5000`)*

2. Botni ishga tushiring:
   ```bash
   python run_bot.py
   ```

## 3. Database (Ma'lumotlar Bazasi) Serveri
**MUHIM:** Hozirgi loyiha **SQLite** dan foydalanadi (`database.sqlite3` fayli).
SQLite fayli odatda bitta serverning ichida turishi kerak. Uni "alohida serverga" shunchaki ko'chirib bo'lmaydi, chunki Web Server unga fayl sifatida ulanadi.

### Yechimlar:
**A) Oddiy yechim (Tavsiya etiladi):**
Databaseni **Web Server** ichida qoldiring. Bot serveri databasaga to'g'ridan-to'g'ri ulanmaydi, u Web Serverdagi API orqali ma'lumot oladi. Shuning uchun Database Web Serverda tursa ham Bot muammosiz ishlayveradi.

**B) Murakkab yechim (PostgreSQL ga o'tish):**
Agar Database haqiqatan ham alohida serverda turishini xohlasangiz, SQLite dan **PostgreSQL** ga o'tish kerak.
Buning qiyinchiligi:
- Kodda minglab SQL so'rovlar `sqlite3` formatida (`?` belgisi bilan) yozilgan.
- PostgreSQL esa `%s` belgisini ishlatadi.
- Barcha SQL querylarni qayta yozib chiqish kerak bo'ladi.

*Hozircha A variantni qo'llab, Web va Botni ajratishingizni maslahat beraman.*

---

## Xulosa: Arxitektura
Sizda 2 ta server bo'ladi:

**Server 1 (Kuchliroq):**
- **Vazifasi:** Web sayt, Admin panel, API va Database.
- **Dastur:** `python run_web.py`
- **Fayllar:** `database.sqlite3` shu yerda turadi.

**Server 2 (Yengilroq):**
- **Vazifasi:** Telegram Bot.
- **Dastur:** `python run_bot.py`
- **Sozlama:** `FLASK_APP_URL` orqali Server 1 ga ulanadi.

Bu usul eng barqaror va tez amalga oshiriladigan usuldir.
