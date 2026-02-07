
import json
import os

def update_seo():
    filepath = "d:/Safety.uz/backend/data/translations.json"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        seo_updates = {
            "ru": {
                "home_title": "Safety.uz - Магазин спецобуви и спецодежды №1",
                "meta_description": "Safety.uz - Лучший выбор сертифицированной спецобуви, рабочей одежды и средств индивидуальной защиты (СИЗ) в Узбекистане. Прямые поставки, гарантия качества и доставка по всей стране.",
                "meta_keywords": "safety.uz, pro obuv, спецобувь, спецодежда, рабочая обувь, спецобувь ташкент, купить спецобувь, защитные ботинки, спецобувь узбекистан, spetsobuv, spestobuv, specobuv, сиз",
                "meta_title_default": "Магазин современной спецобуви и одежды"
            },
            "uz": {
                "home_title": "Safety.uz - Maxsus poyabzallar va ish kiyimlari do'koni",
                "meta_description": "Safety.uz - O'zbekistondagi eng yaxshi maxsus poyabzallar, ish kiyimlari va shaxsiy himoya vositalari (SHHV) do'koni. Sifatli mahsulotlar, kafolat va butun O'zbekiston bo'ylab yetkazib berish.",
                "meta_keywords": "safety.uz, pro obuv, maxsus poyabzal, ish kiyimi, poyafzal, spetsobuv, spestobuv, specobuv, ish kiyimlari toshkent, maxsus kiyimlar, maxsus kiyim sotib olish",
                "meta_title_default": "Zamonaviy maxsus kiyim va poyabzallar do'koni"
            },
            "en": {
                "home_title": "Safety.uz - #1 Safety Footwear & Workwear Store",
                "meta_description": "Safety.uz - The premier supplier of certified safety footwear, work clothing, and personal protective equipment (PPE) in Uzbekistan. High quality, wide range, and nationwide delivery.",
                "meta_keywords": "safety.uz, pro obuv, safety footwear, workwear, protective boots, buy safety shoes, work clothes uzbekistan, ppe, spetsobuv, spestobuv, industrial safety",
                "meta_title_default": "Modern Safety Footwear & Apparel"
            },
            "kz": {
                "home_title": "Safety.uz - №1 Арнайы аяқ киім және жұмыс киімі дүкені",
                "meta_description": "Safety.uz - Өзбекстандағы сертификатталған арнайы аяқ киімдерді, жұмыс киімдері мен жеке қорғаныс құралдарын (ЖҚҚ) жеткізуші. Сапалы өнімдер, кең ассортимент және бүкіл ел бойынша жеткізу.",
                "meta_keywords": "safety.uz, pro obuv, арнайы аяқ киім, жұмыс киімі, қорғаныс етіктері, арнайы киім сатып алу, жққ, spetsobuv, spestobuv, өнеркәсіптік қауіпсіздік",
                "meta_title_default": "Заманауи арнайы киім және аяқ киім дүкені"
            }
        }

        for lang, updates in seo_updates.items():
            if lang in data:
                data[lang].update(updates)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully updated SEO translations in {filepath}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_seo()
