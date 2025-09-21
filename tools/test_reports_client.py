import os, sys, json, traceback

# Ensure project root is on sys.path so we can import top-level modules when running from tools/
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Prevent heavy db/executor init in app module if supported
os.environ["SKIP_DB_INIT"] = "1"

try:
    import app

    client = app.app.test_client()
    resp = client.get("/api/super-admin/reports?type=daily")
    print("STATUS", resp.status_code)
    try:
        j = resp.get_json()
        print(json.dumps(j, ensure_ascii=False, indent=2))
    except Exception:
        print("Response text:")
        print(resp.data.decode("utf-8", errors="replace"))
except Exception:
    traceback.print_exc()
