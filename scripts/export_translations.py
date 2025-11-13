"""Export translations from data/translations.json into per-language files

Usage:
    python scripts/export_translations.py

This will produce files:
    data/translations_ru.json
    data/translations_uz.json
    data/translations_en.json
    data/translations_kz.json

and print a short summary to stdout.
"""
import json
import os

SRC = os.path.join(os.path.dirname(__file__), '..', 'data', 'translations.json')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
LANGS = ['ru', 'uz', 'en', 'kz']


def flatten(node, prefix=''):
    flat = {}
    if isinstance(node, dict):
        for k, v in node.items():
            nk = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flat.update(flatten(v, nk))
            else:
                flat[nk] = v
    return flat


def main():
    try:
        with open(SRC, 'r', encoding='utf-8') as f:
            all_trans = json.load(f)
    except Exception as e:
        print(f"Failed to load translations from {SRC}: {e}")
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    summary = {}
    for lang in LANGS:
        data = all_trans.get(lang, {})
        out_path = os.path.join(OUT_DIR, f"translations_{lang}.json")
        try:
            with open(out_path, 'w', encoding='utf-8') as of:
                json.dump(data, of, ensure_ascii=False, indent=2)
            flat = flatten(data)
            summary[lang] = {'top_level_keys': list(data.keys())[:20], 'flat_count': len(flat), 'file': out_path}
        except Exception as e:
            print(f"Failed to write {out_path}: {e}")

    print("Translations export summary:")
    for lang, info in summary.items():
        print(f"- {lang}: {info['flat_count']} strings -> {info['file']}")
        print(f"  sample keys: {', '.join(info['top_level_keys'])}")

    print("Done.")


if __name__ == '__main__':
    main()
