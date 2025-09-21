"""
News API Endpoints for Pro-Obuv Application
Yangiliklar va reklamalar uchun API endpointlari
"""

import json
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
import uuid

# Blueprint yaratish
news_api = Blueprint("news_api", __name__)

# Ma'lumotlar fayli yo'li
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
NEWS_FILE = os.path.join(DATA_DIR, "news.json")

# Media fayllari uchun yo'llar
MEDIA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "media", "news"
)
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB


def ensure_directories():
    """Kerakli papkalarni yaratish"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "images"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_DIR, "temp"), exist_ok=True)


def load_news_data():
    """JSON fayldan yangiliklar ma'lumotlarini yuklash"""
    try:
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Default data
            default_data = {
                "news": [],
                "metadata": {
                    "total_count": 0,
                    "active_count": 0,
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                    "version": "1.0",
                },
            }
            save_news_data(default_data)
            return default_data
    except Exception as e:
        current_app.logger.error(f"Error loading news data: {str(e)}")
        return {"news": [], "metadata": {"total_count": 0, "active_count": 0}}


def save_news_data(data):
    """Yangiliklar ma'lumotlarini JSON faylga saqlash"""
    try:
        ensure_directories()

        # Metadata yangilash
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"
        data["metadata"]["total_count"] = len(data["news"])
        data["metadata"]["active_count"] = len(
            [n for n in data["news"] if n.get("is_active", False)]
        )

        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        current_app.logger.error(f"Error saving news data: {str(e)}")
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

        # Query parametrlarni tekshirish
        active_only = request.args.get("active", "").lower() == "true"
        news_type = request.args.get("type", "")
        limit = request.args.get("limit", type=int)

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
        # Session tekshirish (bu yerda sizning session mantiqingiz bo'lishi kerak)
        # if not session.get('super_admin'):
        #     return jsonify({"success": False, "message": "Admin huquqi kerak"}), 403

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
        # JSON ma'lumotlarni olish
        news_data = request.get_json()

        if not news_data:
            return jsonify({"success": False, "message": "Ma'lumotlar topilmadi"}), 400

        # Majburiy maydonlarni tekshirish
        if not news_data.get("title", "").strip():
            return (
                jsonify({"success": False, "message": "Sarlavha kiritilishi shart"}),
                400,
            )

        # Mavjud ma'lumotlarni yuklash
        data = load_news_data()

        # Yangi ID generatsiya qilish
        max_id = max([n.get("id", 0) for n in data["news"]], default=0)
        new_id = max_id + 1

        # Yangi yangilik yaratish
        new_news = {
            "id": new_id,
            "title": news_data.get("title", "").strip(),
            "content": news_data.get("content", "").strip(),
            "type": news_data.get("type", "news"),
            "is_active": news_data.get("is_active", True),
            "display_order": news_data.get("display_order", len(data["news"]) + 1),
            "image_url": news_data.get("image_url", ""),
            "video_url": news_data.get("video_url", ""),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }

        # Ro'yxatga qo'shish
        data["news"].append(new_news)

        # Saqlash
        if save_news_data(data):
            return jsonify(
                {
                    "success": True,
                    "message": "Yangilik muvaffaqiyatli qo'shildi",
                    "news": new_news,
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Saqlashda xatolik yuz berdi"}),
                500,
            )

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
        news_data = request.get_json()

        if not news_data:
            return jsonify({"success": False, "message": "Ma'lumotlar topilmadi"}), 400

        # Majburiy maydonlarni tekshirish
        if not news_data.get("title", "").strip():
            return (
                jsonify({"success": False, "message": "Sarlavha kiritilishi shart"}),
                400,
            )

        # Mavjud ma'lumotlarni yuklash
        data = load_news_data()

        # Yanglikni topish
        news_item = None
        for i, news in enumerate(data["news"]):
            if news.get("id") == news_id:
                news_item = news
                break

        if not news_item:
            return jsonify({"success": False, "message": "Yangilik topilmadi"}), 404

        # Ma'lumotlarni yangilash
        news_item.update(
            {
                "title": news_data.get("title", "").strip(),
                "content": news_data.get("content", "").strip(),
                "type": news_data.get("type", news_item.get("type", "news")),
                "is_active": news_data.get(
                    "is_active", news_item.get("is_active", True)
                ),
                "display_order": news_data.get(
                    "display_order", news_item.get("display_order", 0)
                ),
                "image_url": news_data.get("image_url", news_item.get("image_url", "")),
                "video_url": news_data.get("video_url", news_item.get("video_url", "")),
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
        )

        # Saqlash
        if save_news_data(data):
            return jsonify(
                {
                    "success": True,
                    "message": "Yangilik muvaffaqiyatli yangilandi",
                    "news": news_item,
                }
            )
        else:
            return (
                jsonify({"success": False, "message": "Saqlashda xatolik yuz berdi"}),
                500,
            )

    except Exception as e:
        current_app.logger.error(f"Error updating news: {str(e)}")
        return (
            jsonify({"success": False, "message": f"Yangilashda xatolik: {str(e)}"}),
            500,
        )


@news_api.route("/api/news/<int:news_id>", methods=["DELETE"])
def delete_news(news_id):
    """Yanglikni o'chirish"""
    try:
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

        # Xavfsiz fayl nomi yaratish
        news_type = request.form.get("news_type", "news")
        news_id = request.form.get("news_id", "new")
        filename = generate_filename(file.filename, news_type, news_id)

        # Fayl turini aniqlash va saqlash yo'lini belgilash
        if is_image:
            upload_path = os.path.join(MEDIA_DIR, "images", filename)
            url_path = f"/static/media/news/images/{filename}"
        else:
            upload_path = os.path.join(MEDIA_DIR, "videos", filename)
            url_path = f"/static/media/news/videos/{filename}"

        # Faylni saqlash
        ensure_directories()
        file.save(upload_path)

        return jsonify(
            {
                "success": True,
                "message": "Fayl muvaffaqiyatli yuklandi",
                "filename": filename,
                "file_url": url_path,
                "file_size": file_size,
                "file_type": "image" if is_image else "video",
            }
        )

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
