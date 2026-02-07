import json
import os

def update_translations():
    path = 'd:/Safety.uz/backend/data/translations.json'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Missing nav.products and enhanced SEO
    updates = {
        "uz": {
            "nav": {
                "products": "Mahsulotlar",
                "home": "Bosh sahifa",
                "menu": "Menyu",
                "news": "Yangiliklar",
                "about": "Biz haqimizda",
                "contact": "Aloqa",
                "downloads": "Yuklamalar",
                "favorites": "Sevimlilar"
            },
            "home_title": "Safety.uz - O'zbekistondagi №1 Maxsus poyabzallar va ish kiyimlari do'koni | Pro Obuv",
            "meta_description": "Safety.uz (Pro Obuv) - O'zbekistonda sertifikatlangan maxsus poyabzallar, ish kiyimlari va shaxsiy himoya vositalari (SHHV) yetkazib beruvchi. Qurilish, sanoat va barcha sohalar uchun xavfsizlik poyabzallari.",
            "meta_keywords": "safety.uz, pro obuv, maxsus poyabzal, ish kiyimi, poyafzal, spetsobuv, spestobuv, specobuv, spesobuv, ish kiyimlari toshkent, maxsus kiyimlar, maxsus kiyim sotib olish, temir burunli poyabzal, xavfsizlik botinkalari, qurilish poyabzali, shhv, shaxsiy himoya vositalari, respirator, kaska, qo'lqop, himoya ko'zoynagi, maxsus etik, dielektrik etik",
            "search_gear_placeholder": "Xavfsizlik jihozlarini qidiring: S3 etiklari, yuqori ko'rinadigan kurtkalar, kompozit burun..."
        },
        "ru": {
            "nav": {
                "products": "Товары",
                "home": "Главная",
                "menu": "Меню",
                "news": "Новости",
                "about": "О компании",
                "contact": "Контакты",
                "downloads": "Загрузки",
                "favorites": "Избранное"
            },
            "home_title": "Safety.uz - Спецобувь и спецодежда №1 в Узбекистане | Pro Obuv",
            "meta_description": "Safety.uz (Pro Obuv) - ваш надежный поставщик сертифицированной спецобуви, рабочей одежды и СИЗ в Узбекистане. Широкий выбор: спецобувь, ботинки с металлическим носком, спецодежда для всех сфер промышленности.",
            "meta_keywords": "safety.uz, pro obuv, спецобувь, спецодежда, рабочая обувь, спецобувь ташкент, купить спецобувь, защитные ботинки, спецобувь узбекистан, spetsobuv, spestobuv, specobuv, spesobuv, сиз, индивидуальная защита, рабочая одежда ташкент, ботинки s3, ботинки s1, военная обувь, строительная обувь, респираторы, каски, перчатки, защитные очки, спецботинки",
            "search_gear_placeholder": "Поиск снаряжения безопасности: ботинки S3, куртки высокой видимости, композитный носок..."
        },
        "en": {
            "nav": {
                "products": "Products",
                "home": "Home",
                "menu": "Menu",
                "news": "News",
                "about": "About Us",
                "contact": "Contact",
                "downloads": "Downloads",
                "favorites": "Favorites"
            },
            "home_title": "Safety.uz - #1 Safety Footwear and Workwear in Uzbekistan | Pro Obuv",
            "meta_description": "Safety.uz (Pro Obuv) - leading supplier of certified safety footwear, workwear, and PPE in Uzbekistan. High-quality safety shoes, boots, and industrial clothing for all sectors.",
            "meta_keywords": "safety.uz, pro obuv, safety footwear, workwear, safety shoes, safety shoes tashkent, buy safety gear, protective boots, safety boots uzbekistan, ppe, personal protective equipment, industrial clothing, s3 boots, s1 shoes, construction footwear, respirators, helmets, gloves, safety glasses",
            "search_gear_placeholder": "Search safety gear: S3 boots, high-visibility jackets, composite toe..."
        },
        "kz": {
            "nav": {
                "products": "Тауарлар",
                "home": "Басты бет",
                "menu": "Мәзір",
                "news": "Жаңалықтар",
                "about": "Біз туралы",
                "contact": "Байланыс",
                "downloads": "Жүктеулер",
                "favorites": "Таңдаулылар"
            },
            "home_title": "Safety.uz - Өзбекстандағы №1 Арнайы аяқ киім және жұмыс киімі дүкені | Pro Obuv",
            "meta_description": "Safety.uz (Pro Obuv) - Өзбекстандағы сертификатталған арнайы аяқ киімдерді, жұмыс киімдері мен ЖҚҚ жеткізуші. Құрылыс және өнеркәсіп салаларына арналған қорғаныс аяқ киімі мен киімі.",
            "meta_keywords": "safety.uz, pro obuv, арнайы аяқ киім, жұмыс киімі, қорғаныс етіктері, арнайы киім сатып алу, жққ, жеке қорғаныс құралдары, spetsobuv, spestobuv, specobuv, spesobuv, өнеркәсіптік қауіпсіздік, қауіпсіздік етіктері ташкент, құрылыс аяқ киімі, респираторлар, каскалар, қолғаптар, қорғаныс көзілдірігі",
            "search_gear_placeholder": "Қауіпсіздік техникасын іздеу: S3 етік, жоғары көрінетін куртка, композиттік табан..."
        }
    }

    for lang, content in updates.items():
        if lang not in data:
            data[lang] = {}
        
        # Merge nav
        if "nav" not in data[lang]:
            data[lang]["nav"] = {}
        data[lang]["nav"].update(content["nav"])
        
        # Merge top level
        for key, value in content.items():
            if key != "nav":
                data[lang][key] = value

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Translations updated successfully.")

if __name__ == "__main__":
    update_translations()
