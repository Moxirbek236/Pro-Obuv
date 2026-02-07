
import json
import os

def update_universal_seo():
    filepath = "d:/Safety.uz/backend/data/translations.json"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Enriched keywords for all languages
        seo_updates = {
            "ru": {
                "home_title": "Safety.uz - Спецобувь и спецодежда №1 в Узбекистане | Pro Obuv",
                "meta_description": "Safety.uz (Pro Obuv) - ваш надежный поставщик сертифицированной спецобуви, рабочей одежды и СИЗ. Широкий выбор: спецобувь, ботинки с металлическим носком, диэлектрические сапоги, спецодежда для всех сфер промышленности.",
                "meta_keywords": "safety.uz, pro obuv, спецобувь, спецодежда, рабочая обувь, спецобувь ташкент, купить спецобувь, защитные ботинки, спецобувь узбекистан, spetsobuv, spestobuv, specobuv, spesobuv, сиз, индивидуальная защита, рабочая одежда ташкент, ботинки s3, ботинки s1, военная обувь, строительная обувь",
                "meta_title_default": "Safety.uz - Качественная спецобувь и СИЗ"
            },
            "uz": {
                "home_title": "Safety.uz - O'zbekistondagi №1 Maxsus poyabzallar va ish kiyimlari do'koni",
                "meta_description": "Safety.uz (Pro Obuv) - sertifikatlangan maxsus poyabzallar, ish kiyimlari va SHHVning ishonchli yetkazib beruvchisi. Maxsus poyabzal, temir burunli botinkalar, dielektrik etiklar va barcha sanoat sohalari uchun ish kiyimlari.",
                "meta_keywords": "safety.uz, pro obuv, maxsus poyabzal, ish kiyimi, poyafzal, spetsobuv, spestobuv, specobuv, spesobuv, ish kiyimlari toshkent, maxsus kiyimlar, maxsus kiyim sotib olish, temir burunli poyabzal, xavfsizlik botinkalari, qurilish poyabzali, shhv, shaxsiy himoya vositalari",
                "meta_title_default": "Safety.uz - Sifatli maxsus kiyim va poyabzallar"
            },
            "en": {
                "home_title": "Safety.uz - #1 Safety Footwear & Workwear Store in Uzbekistan | Pro Obuv",
                "meta_description": "Safety.uz (Pro Obuv) - your reliable supplier of certified safety footwear, work clothing, and PPE. Wide selection: safety shoes, steel toe boots, dielectric boots, and workwear for all industrial sectors.",
                "meta_keywords": "safety.uz, pro obuv, safety footwear, workwear, protective boots, buy safety shoes, work clothes uzbekistan, ppe, spetsobuv, spestobuv, specobuv, spesobuv, industrial safety, personal protective equipment, safety boots tashkent, s3 boots, s1 boots, construction shoes",
                "meta_title_default": "Safety.uz - Professional Safety Gear & PPE"
            },
            "kz": {
                "home_title": "Safety.uz - Өзбекстандағы №1 Арнайы аяқ киім және жұмыс киімі дүкені | Pro Obuv",
                "meta_description": "Safety.uz (Pro Obuv) - сертификатталған арнайы аяқ киімдерді, жұмыс киімдері мен ЖҚҚ жеткізуші. Арнайы аяқ киім, темір тұмсықты етіктер, диэлектрик етіктер және барлық өнеркәсіп салаларына арналған жұмыс киімдері.",
                "meta_keywords": "safety.uz, pro obuv, арнайы аяқ киім, жұмыс киімі, қорғаныс етіктері, арнайы киім сатып алу, жққ, spetsobuv, spestobuv, specobuv, spesobuv, өнеркәсіптік қауіпсіздік, жеке қорғаныс құралдары, қауіпсіздік етіктері ташкент, құрылыс аяқ киімі",
                "meta_title_default": "Safety.uz - Сапалы арнайы киім және аяқ киім"
            }
        }

        for lang, updates in seo_updates.items():
            if lang in data:
                data[lang].update(updates)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully updated universal SEO translations in {filepath}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_universal_seo()
