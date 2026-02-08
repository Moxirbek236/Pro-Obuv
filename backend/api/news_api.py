# News API Endpoints for Pro-Obuv Application
# Yangiliklar va reklamalar uchun API endpointlari

import json
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app, session
import uuid
from services.cloudinary_service import cloudinary_service
from cloudinary_helpers import get_cloudinary_url

news_api = Blueprint("news_api", __name__)

# Social footer appended to every news content
SOCIAL_FOOTER = (
    "\nYoutube: https://www.youtube.com/@proobuv-safety\n"
    "Telegram: https://t.me/specobuv\n"
    " Instagram: https://www.instagram.com/proguarduz/\n"
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NEWS_FILE = os.path.join(DATA_DIR, "news.json")

# MEDIA_DIR is no longer used for local storage (migrated to Cloudinary)
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB


def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "images"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "temp"), exist_ok=True)


def load_news_data():
    """Load news from the database. Returns a dict with keys 'news' and 'metadata'.

    This function queries the application's database (via `execute_query`) so
    the application no longer depends on `data/news.json` as the primary source.
    """
    try:
        # Import lazily to avoid circular imports at module load
        from app import execute_query

        rows = execute_query(
            "SELECT * FROM news ORDER BY display_order ASC, created_at DESC",
            fetch_all=True,
        ) or []

        # compute metadata
        total = execute_query("SELECT COUNT(1) FROM news", fetch_one=True)[0]
        active = execute_query("SELECT COUNT(1) FROM news WHERE is_active = 1", fetch_one=True)[0]

        # Normalize rows into plain dicts
        news_list = []
        for r in rows:
            try:
                n = dict(r) if hasattr(r, 'keys') else r
                # Normalize multi-media fields: support images_json/videos_json (JSON text) and legacy image_url/video_url
                try:
                    # images: stored as JSON string in images_json
                    if isinstance(n.get('images_json'), str) and n.get('images_json'):
                        try:
                            n['images'] = json.loads(n.get('images_json') or '[]') or []
                        except Exception:
                            n['images'] = []
                    else:
                        # fall back to legacy single image_url
                        n['images'] = [n.get('image_url')] if n.get('image_url') else []

                    # videos: stored as JSON string in videos_json
                    if isinstance(n.get('videos_json'), str) and n.get('videos_json'):
                        try:
                            n['videos'] = json.loads(n.get('videos_json') or '[]') or []
                        except Exception:
                            n['videos'] = []
                    else:
                        n['videos'] = [n.get('video_url')] if n.get('video_url') else []

                    # Compute per-video youtube embeds
                    embeds = []
                    for v in (n.get('videos') or []):
                        try:
                            e = extract_youtube_embed_local(v or '')
                            embeds.append(e)
                        except Exception:
                            embeds.append(None)
                    n['youtube_embeds'] = embeds

                    # Optimize Cloudinary URLs
                    if n.get('images'):
                        n['images'] = [get_cloudinary_url(img) for img in n['images'] if img]
                    if n.get('image_url'):
                        n['image_url'] = get_cloudinary_url(n['image_url'])
                    if n.get('videos'):
                         n['videos'] = [get_cloudinary_url(vid, resource_type="video") for vid in n['videos'] if vid]
                    if n.get('video_url'):
                         n['video_url'] = get_cloudinary_url(n['video_url'], resource_type="video")
                except Exception:
                    n.setdefault('images', [])
                    n.setdefault('videos', [])
                    n.setdefault('youtube_embeds', [])

                news_list.append(n)
            except Exception:
                news_list.append(r)

        return {
            "news": news_list,
            "metadata": {
                "total_count": int(total) if total is not None else len(news_list),
                "active_count": int(active) if active is not None else len([n for n in news_list if n.get('is_active')]),
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "version": "db",
            },
        }
    except Exception as e:
        current_app.logger.error(f"Error loading news data from DB: {str(e)}")
        return {"news": [], "metadata": {"total_count": 0, "active_count": 0}}


def extract_youtube_embed_local(url: str):
    """Return a normalized YouTube embed URL for a given YouTube video link, or None."""
    try:
        if not url:
            return None
        import re

        u = url.strip()
        m = re.search(r'(?:v=|\/embed\/|youtu\.be\/)([A-Za-z0-9_\-]{11})', u)
        if m:
            return f"https://www.youtube.com/embed/{m.group(1)}"
    except Exception:
        return None
    return None


def save_news_data(data):
    """Placeholder: saving to JSON is deprecated when DB-backed mode is active; no-op."""
    current_app.logger.warning("save_news_data called but DB-backed mode is active; no-op")
    return False


def allowed_file(filename, file_type="image"):
    """Fayl kengaytmasi tekshirish"""
    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    if file_type == "image":
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == "video":
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False


def generate_filename(original_filename, news_type="news", news_id=None):
    """Yangi fayl nomi generatsiya qilish"""
    if "." in original_filename:
        ext = original_filename.rsplit(".", 1)[1].lower()
    else:
        ext = "jpg"  # default

    timestamp = int(time.time())
    news_id = news_id or "new"
    prefix = "ad" if news_type == "advertisement" else "news"

    return f"{prefix}_{news_id}_{timestamp}.{ext}"


@news_api.route("/api/news", methods=["GET"])
def get_all_news():
    """Barcha yangiliklar ro'yxatini olish"""
    try:
        data = load_news_data()
        news_list = data.get("news", [])

        # Backwards compatibility: ensure each item has images/videos arrays and youtube_embeds
        for i, n in enumerate(news_list):
            try:
                if not isinstance(n, dict):
                    news_list[i] = dict(n)
                    n = news_list[i]
                n.setdefault('images', [])
                n.setdefault('videos', [])
                # youtube_embeds populated in load_news_data normalization; ensure key exists
                n.setdefault('youtube_embeds', [])
                # Backwards-compat: provide single youtube_embed key for legacy consumers
                n['youtube_embed'] = (n['youtube_embeds'][0] if n['youtube_embeds'] and len(n['youtube_embeds'])>0 else None)
            except Exception:
                continue

        # Query parametrlarni tekshirish
        active_only = request.args.get("active", "").lower() == "true"
        news_type = request.args.get("type", "")
        limit = request.args.get("limit", type=int)
        # Language selection: api consumers can request 'lang' (uz/ru/en/kz)
        lang = request.args.get("lang") or None

        # Filtrlash
        if active_only:
            news_list = [n for n in news_list if n.get("is_active", False)]

        if news_type:
            news_list = [n for n in news_list if n.get("type", "") == news_type]

        # Tartibga solish (display_order bo'yicha, keyin sana bo'yicha)
        news_list.sort(
            key=lambda x: (x.get("display_order", 999), x.get("created_at", ""))
        )

        # Limit qo'llash
        if limit and limit > 0:
            news_list = news_list[:limit]

        # If lang provided, compute localized_title/localized_content for each item
        if lang:
            for i, n in enumerate(news_list):
                try:
                    # prefer per-language fields title_<lang> / content_<lang>, fall back to legacy title/content
                    n["localized_title"] = (
                        n.get(f"title_{lang}") or n.get("title") or ""
                    )
                    n["localized_content"] = (
                        n.get(f"content_{lang}") or n.get("content") or ""
                    )
                except Exception:
                    n["localized_title"] = n.get("title") or ""
                    n["localized_content"] = n.get("content") or ""

        return jsonify(
            {
                "success": True,
                "news": news_list,
                "total_count": len(news_list),
                "metadata": data.get("metadata", {}),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting news: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Yangiliklar yuklanishida xatolik: {str(e)}",
                }
            ),
            500,
        )


@news_api.route("/api/news/active", methods=["GET"])
def get_active_news():
    """Faqat faol yangiliklar ro'yxatini olish"""
    return get_all_news()  # active=true parametr bilan


@news_api.route("/api/news/admin", methods=["GET"])
def get_admin_news():
    """Admin uchun barcha yangiliklar (faol va nofaol)"""
    try:
        # Require super_admin in session to access admin APIs
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        data = load_news_data()
        return jsonify(
            {
                "success": True,
                "news": data.get("news", []),
                "metadata": data.get("metadata", {}),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error getting admin news: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Ma'lumotlar yuklanishida xatolik: {str(e)}",
                }
            ),
            500,
        )


@news_api.route("/api/news", methods=["POST"])
def create_news():
    """Yangi yangilik qo'shish"""
    try:
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        # JSON ma'lumotlarni olish
        news_data = request.get_json()

        if not news_data:
            return jsonify({"success": False, "message": "Ma'lumotlar topilmadi"}), 400

        # Majburiy maydonlarni tekshirish
        # Accept either legacy 'title' or any of title_uz/title_ru/title_en/title_kz
        title_present = any(
            (news_data.get(f"title_{lang}") or "").strip() for lang in ("uz", "ru", "en", "kz")
        ) or (news_data.get("title") or "").strip()
        if not title_present:
            return (
                jsonify({"success": False, "message": "Sarlavha kiritilishi shart"}),
                400,
            )

        # Persist to DB
        from app import execute_query, get_column_names

        # Determine available columns on the news table
        available_cols = get_column_names("news")

        now = datetime.utcnow().isoformat() + "Z"

        # Build insert column list and values
        insert_map = {
            'title': (news_data.get('title') or '').strip(),
            'content': (news_data.get('content') or '').strip(),
            'type': news_data.get('type', 'news'),
            'image_url': news_data.get('image_url', ''),
            'video_url': news_data.get('video_url', ''),
            # Support arrays: images/videos stored as JSON in images_json/videos_json columns if available
            'images_json': json.dumps(news_data.get('images') or []) if news_data.get('images') is not None else None,
            'videos_json': json.dumps(news_data.get('videos') or []) if news_data.get('videos') is not None else None,
            'is_active': 1 if news_data.get('is_active', True) else 0,
            'display_order': news_data.get('display_order', 0) or 0,
            'created_at': now,
            'updated_at': now,
        }
        for lang in ('uz', 'ru', 'en', 'kz'):
            insert_map[f'title_{lang}'] = (news_data.get(f'title_{lang}') or '').strip()
            insert_map[f'content_{lang}'] = (news_data.get(f'content_{lang}') or '').strip()

        insert_cols = [c for c in insert_map.keys() if c in available_cols]
        values = [insert_map[c] for c in insert_cols]

        if not insert_cols:
            return jsonify({'success': False, 'message': 'No writable columns available'}), 500

        placeholders = ','.join(['?'] * len(insert_cols))
        sql = f"INSERT INTO news ({','.join(insert_cols)}) VALUES ({placeholders})"
        lastid = execute_query(sql, params=tuple(values))
        new_item = execute_query("SELECT * FROM news WHERE id = ?", (lastid,), fetch_one=True)
        return jsonify({'success': True, 'message': 'Yangilik muvaffaqiyatli qo\'shildi', 'news': dict(new_item) if new_item else {}})

    except Exception as e:
        current_app.logger.error(f"Error creating news: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Qo'shishda xatolik: {str(e)}"}),
            500,
        )


@news_api.route("/api/news/<int:news_id>", methods=["PUT"])
def update_news(news_id):
    """Yanglikni yangilash"""
    try:
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        news_data = request.get_json()

        if not news_data:
            return jsonify({"success": False, "message": "Ma'lumotlar topilmadi"}), 400

        # Majburiy maydonlarni tekshirish - accept either legacy title or one of per-language titles
        title_present = any(
            (news_data.get(f"title_{lang}") or "").strip() for lang in ("uz", "ru", "en", "kz")
        ) or (news_data.get("title") or "").strip()
        if not title_present:
            return (
                jsonify({"success": False, "message": "Sarlavha kiritilishi shart"}),
                400,
            )

        from app import execute_query, get_column_names

        cols_info = get_column_names("news")
        available_cols = cols_info

        # Find existing
        existing = execute_query("SELECT * FROM news WHERE id = ?", (news_id,), fetch_one=True)
        if not existing:
            return jsonify({"success": False, "message": "Yangilik topilmadi"}), 404

        update_map = {}
        update_map['title'] = (news_data.get('title') or (existing.get('title') if hasattr(existing,'get') else (existing[1] if len(existing) > 1 else '')) or '').strip()
        update_map['content'] = (news_data.get('content') or existing.get('content') or '').strip()
        for lang in ('uz','ru','en','kz'):
            tkey = f'title_{lang}'
            ckey = f'content_{lang}'
            if tkey in news_data:
                update_map[tkey] = (news_data.get(tkey) or '').strip()
            if ckey in news_data:
                update_map[ckey] = (news_data.get(ckey) or '').strip()

        update_map['type'] = news_data.get('type', existing.get('type','news'))
        update_map['is_active'] = 1 if news_data.get('is_active', existing.get('is_active',1)) else 0
        update_map['display_order'] = news_data.get('display_order', existing.get('display_order',0))
        update_map['image_url'] = news_data.get('image_url', existing.get('image_url',''))
        update_map['video_url'] = news_data.get('video_url', existing.get('video_url',''))
        # Accept arrays; store as JSON text if provided
        if 'images' in news_data:
            update_map['images_json'] = json.dumps(news_data.get('images') or [])
        if 'videos' in news_data:
            update_map['videos_json'] = json.dumps(news_data.get('videos') or [])
        update_map['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        set_cols = [k for k in update_map.keys() if k in available_cols]
        if not set_cols:
            return jsonify({'success': False, 'message': 'No updatable columns available'}), 500

        sql = 'UPDATE news SET ' + ','.join([f"{c} = ?" for c in set_cols]) + ' WHERE id = ?'
        params = [update_map[c] for c in set_cols] + [news_id]
        execute_query(sql, params=tuple(params))
        updated = execute_query('SELECT * FROM news WHERE id = ?', (news_id,), fetch_one=True)
        return jsonify({'success': True, 'message':'Yangilik muvaffaqiyatli yangilandi','news': dict(updated) if updated else {}})

    except Exception as e:
        current_app.logger.error(f"Error updating news: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Yangilashda xatolik: {str(e)}"}),
            500,
        )


@news_api.route("/api/news/<int:news_id>", methods=["GET"])
def get_single_news(news_id):
    """Return a single news item by id (for admin edit)."""
    try:
        data = load_news_data()
        for n in data.get("news", []):
            if n.get("id") == news_id:
                # Normalize media arrays and youtube embeds for the single item
                n_obj = dict(n) if isinstance(n, dict) else n
                try:
                    if isinstance(n_obj.get('images_json'), str) and n_obj.get('images_json'):
                        n_obj['images'] = json.loads(n_obj.get('images_json') or '[]') or []
                    else:
                        n_obj['images'] = [n_obj.get('image_url')] if n_obj.get('image_url') else []
                except Exception:
                    n_obj['images'] = []
                try:
                    if isinstance(n_obj.get('videos_json'), str) and n_obj.get('videos_json'):
                        n_obj['videos'] = json.loads(n_obj.get('videos_json') or '[]') or []
                    else:
                        n_obj['videos'] = [n_obj.get('video_url')] if n_obj.get('video_url') else []
                except Exception:
                    n_obj['videos'] = []
                # compute youtube_embeds
                embeds = []
                for v in (n_obj.get('videos') or []):
                    try:
                        embeds.append(extract_youtube_embed_local(v or '') )
                    except Exception:
                        embeds.append(None)
                n_obj['youtube_embeds'] = embeds
                return jsonify({"success": True, "news": n_obj})

        return jsonify({"success": False, "message": "Yangilik topilmadi"}), 404
    except Exception as e:
        current_app.logger.error(f"Error getting single news: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Ma'lumot yuklashda xatolik: {str(e)}"}),
            500,
        )


@news_api.route("/api/news/<int:news_id>", methods=["DELETE"])
def delete_news(news_id):
    """Yanglikni o'chirish"""
    try:
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        data = load_news_data()

        # Yanglikni topish va o'chirish
        initial_count = len(data["news"])
        data["news"] = [news for news in data["news"] if news.get("id") != news_id]

        if len(data["news"]) == initial_count:
            return jsonify({"success": False, "message": "Yangilik topilmadi"}), 404

        # Saqlash
        if save_news_data(data):
            return jsonify(
                {"success": True, "message": "Yangilik muvaffaqiyatli o'chirildi"}
            )
        else:
            return (
                jsonify({"success": False, "message": "O'chirishda xatolik yuz berdi"}),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error deleting news: {str(e)}")
        return (
            jsonify({"success": False, "message": f"O'chirishda xatolik: {str(e)}"}),
            500,
        )


@news_api.route("/api/news/toggle/<int:news_id>", methods=["POST"])
def toggle_news_status(news_id):
    """Yangilik holatini o'zgartirish (faol/nofaol)"""
    try:
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        data = load_news_data()

        # Yanglikni topish
        news_item = None
        for news in data["news"]:
            if news.get("id") == news_id:
                news_item = news
                break

        if not news_item:
            return jsonify({"success": False, "message": "Yangilik topilmadi"}), 404

        # Holatni o'zgartirish
        new_status = not news_item.get("is_active", False)
        news_item["is_active"] = new_status
        news_item["updated_at"] = datetime.utcnow().isoformat() + "Z"

        # Saqlash
        if save_news_data(data):
            status_text = "faollashtirildi" if new_status else "nofaol qilindi"
            return jsonify(
                {
                    "success": True,
                    "message": f"Yangilik {status_text}",
                    "is_active": new_status,
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Saqlashda xatolik yuz berdi"}),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error toggling news status: {str(e)}")
        return (
            jsonify(
                {"success": False, "message": f"Holat o'zgartirishda xatolik: {str(e)}"}
            ),
            500,
        )


@news_api.route("/admin/upload-news-media", methods=["POST"])
def upload_media():
    """Media fayl yuklash (rasmlar va videolar)"""
    try:
        if not session.get("super_admin"):
            return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

        if "file" not in request.files:
            return jsonify({"success": False, "message": "Fayl tanlanmadi"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "Fayl tanlanmadi"}), 400

        # Fayl turini aniqlash
        is_image = allowed_file(file.filename, "image")
        is_video = allowed_file(file.filename, "video")

        if not (is_image or is_video):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Noto'g'ri fayl formati. Faqat rasm va video fayllar qabul qilinadi.",
                    }
                ),
                400,
            )

        # Fayl o'lchamini tekshirish
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_size = MAX_IMAGE_SIZE if is_image else MAX_VIDEO_SIZE
        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Fayl hajmi {size_mb}MB dan oshmasligi kerak",
                    }
                ),
                400,
            )

        # Cloudinary upload logic
        try:
            folder = "news/images" if is_image else "news/videos"
            resource_type = "image" if is_image else "video"
            
            # Use a thread pool for asynchronous-style handling if needed, 
            # but here we need the URL for the response. 
            # Streaming directly from file.stream to Cloudinary.
            upload_result = cloudinary_service.upload_image(
                file.stream,
                folder=folder,
                resource_type=resource_type
            )
            
            if not upload_result:
                return jsonify({"success": False, "message": "Cloudinary upload failed"}), 500
                
            url_path = upload_result.get("secure_url")
            public_id = upload_result.get("public_id")
            # For backward compatibility with clients expecting a filename
            res_filename = secure_filename(file.filename)

            return jsonify(
                {
                    "success": True,
                    "message": "Fayl muvaffaqiyatli yuklandi",
                    "filename": res_filename,
                    "file_url": url_path,
                    "public_id": public_id,
                    "file_size": file_size,
                    "file_type": "image" if is_image else "video",
                }
            )
        except Exception as upload_err:
            current_app.logger.error(f"Cloudinary upload error: {str(upload_err)}")
            return jsonify({"success": False, "message": f"Cloudinary upload error: {str(upload_err)}"}), 500

    except Exception as e:
        # Detailed logging for easier debugging: include stack trace and context
        import traceback

        tb = traceback.format_exc()
        try:
            context_info = {
                "filename": getattr(file, "filename", None),
                "detected_image": is_image if "is_image" in locals() else None,
                "detected_video": is_video if "is_video" in locals() else None,
                "file_size": file_size if "file_size" in locals() else None,
                "upload_path": upload_path if "upload_path" in locals() else None,
            }
        except Exception:
            context_info = {}

        current_app.logger.error(
            f"Error uploading media: {str(e)} | context: {context_info}\nTraceback:\n{tb}"
        )
        return (
            jsonify({"success": False, "message": f"Fayl yuklashda xatolik: {str(e)}"}),
            500,
        )


# Error handlers (blueprint uchun)
@news_api.errorhandler(404)
def news_api_not_found(error):
    return jsonify({"success": False, "message": "API endpoint topilmadi"}), 404


@news_api.errorhandler(500)
def news_api_internal_error(error):
    return jsonify({"success": False, "message": "Ichki server xatosi"}), 500


# Blueprint ni Flask app ga qo'shish uchun function
def register_news_api(app):
    """News API ni Flask app ga ro'yxatdan o'tkazish"""
    app.register_blueprint(news_api)


# Agar bu fayl to'g'ridan-to'g'ri ishga tushirilsa, test qilish
if __name__ == "__main__":
    from flask import Flask

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-key"
    register_news_api(app)

    print("News API test server ishga tushmoqda...")
    app.run(debug=True, port=5001)
