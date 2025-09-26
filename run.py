import os

try:
    # Preferred factory pattern
    from app import create_app  # type: ignore

    app = create_app()
except Exception:
    # Fallback to direct app instance
    from app import app  # type: ignore

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", os.environ.get("PORT", "8001")))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
