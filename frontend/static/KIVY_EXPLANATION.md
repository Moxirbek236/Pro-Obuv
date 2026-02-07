# Python (Kivy) orqali APK yaratish

Siz Python va Kivy orqali ilova yaratishni so'radingiz. Men buning uchun kerakli fayllarni (`main.py` va `buildozer.spec`) tayyorlab, `static/kivy_project/` papkasiga joyladim.

### ⚠️ Muhim Ogohlantirish
Sizning **Safety.uz** loyihangiz bu — **Web Sayt** (HTML/CSS/JS). Kivy esa — **Native Ilovalar** (Python Buttons/Widgets) yasash uchun freymvork.

Quyidagi sabablarga ko'ra bu usulni **qattiq tavsiya etmayman**:
1. **Dizayn yo'qoladi**: Saytingizdagi chiroyli dizayn, animatsiyalar va jadval Kivy da ishlamaydi. Hammasini qaytadan noldan yozib chiqish kerak.
2. **Katta hajm**: Oddiy "Hello World" Kivy dasturi ham 20MB dan oshadi (PWA esa <1MB).
3. **Qiyin yangilash**: Saytda o'zgarish qilsangiz, APK ni ham qayta kompilyatsiya qilib, foydalanuvchilarga tarqatish kerak. PWA da esa avtomatik yangilanadi.

### Agar baribir Kivy orqali qilmoqchi bo'lsangiz:

Men sizga yaratib bergan `main.py` fayli bu **Launcher**. Ya'ni u shunchaki tugma ko'rsatadi va uni bosganda foydalanuvchining brauzerida sizning Admin panelingizni ochib beradi.

**APK ga aylantirish uchun yo'riqnoma:**
(Bu jarayon faqat **Linux** yoki **Mac** kompyuterida ishlaydi. Windows da qilish juda qiyin).

1. Kompyuterga kerakli kutubxonalarni o'rnating:
   ```bash
   pip install buildozer cython kivy
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   ```

2. `kivy_project` papkasiga kiring:
   ```bash
   cd static/kivy_project
   ```

3. APK ni kompilyatsiya qiling:
   ```bash
   buildozer android debug
   ```
   (Bu jarayon internet tezligiga qarab 30-60 daqiqa vaqt olishi mumkin).

4. Tayyor `.apk` fayl `bin/` papkasida paydo bo'ladi.

---

### Mening Tavsiyam: 1-variant (PWA)
Siz baribir "webbrowser.open" ishlatayotganingiz uchun, bu Kivy ilovasi shunchaki "ortiqcha yuk" bo'lib qoladi. Eng yaxshisi:
1. `downloads.html` dagi **PWABuilder** yo'riqnomasi orqali haqiqiy, yengil va Play Market qabul qiladigan APK oling.
2. Bu APK to'g'ridan-to'g'ri ilova ichida saytni ochadi va xuddi native ilovadek ishlaydi.
