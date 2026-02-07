# Android APK/AAB Yaratish Qo'llanmasi (Google Play Uchun)

Sizning Safety.uz tizimingiz hozirda to'liq **Progressive Web App (PWA)** standartlariga javob beradi. Google Play Marketga joylash uchun sizga **.aab** (Android App Bundle) fayli kerak bo'ladi.

Men AI sifatida to'g'ridan-to'g'ri kompilyatsiya qilingan (binary) fayllarni yarata olmayman, lekin siz quyidagi 3 qadamda Google Play uchun tayyor faylni bepul olishingiz mumkin.

### 1-qadam: Saytni Texnik Tayyorlash (Bajarildi ✅)
Men siz uchun kerakli barcha fayllarni tayyorladim:
- `manifest.json`: Ilova nomi, ikonkalar va sozlamalar Play Market talablariga moslandi.
- `sw.js`: Ilova oflayn ishlashi va tez yuklanishi uchun keshlovchi xizmat.
- Mobil dizayn: Super Admin paneli mobil qurilmalarga to'liq moslashtirildi.

### 2-qadam: APK/AAB Faylni Olish (2 daqiqa)
Buning uchun Microsoft va Google tomonidan ishlab chiqilgan rasmiy **PWABuilder** xizmatidan foydalanamiz.

1. **https://www.pwabuilder.com/** saytiga kiring.
2. Saytingiz manzilini kiritib (masalan: `https://safety.uz` yoki deploy qilingan url) **Start** tugmasini bosing.
3. Tizim sizning saytingizni tekshiradi. Hamma narsa yashil bo'lishi kerak.
4. **Package for Stores** tugmasini bosing.
5. **Android** bo'limidan **Generate** tugmasini bosing.
6. Quyidagi sozlamalarni tanlang:
   - **Signing Key**: "Create New" (yangi kalit yaratish).
   - Barcha ma'lumotlarni to'ldiring va **Download** qiling.

Sizga `.zip` fayl yuklanadi. Uning ichida:
- `assetlinks.json` (buni saytingizga joylaysiz)
- `signed.apk` (test qilish uchun)
- `signed.aab` (**Google Play ga yuklash uchun shu fayl kerak**)

### 3-qadam: Google Play ga Joylash
Olingan `.aab` faylni Google Play Console orqali bemalol yuklashingiz mumkin. Bu ilova Android 4.4 dan boshlab eng yangi versiyalarigacha (Android 14+) muammosiz ishlaydi.

---
**Eslatma:** Hozirgi `downloads` sahifasidagi APK fayl faqat namuna edi. Haqiqiy ishlaydigan faylni olish uchun yuqoridagi usuldan foydalanish eng to'g'ri va xavfsiz yo'ldir.
