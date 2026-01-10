import traceback
import json
import datetime
import time

print("TEST START")
try:
    print("IMPORT APP...")
    from app import app

    print("APP IMPORTED")
    c = app.test_client()
    today = datetime.date.today().strftime("%Y-%m-%d")
    print("SENDING REQUEST...")
    resp = c.get(f"/api/super-admin/reports?start_date={today}&end_date={today}")
    print("RESPONSE RECEIVED")
    print("STATUS:", resp.status_code)
    data = resp.get_json()
    print("JSON:", json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print("EXCEPTION:")
    traceback.print_exc()
    print("ERR:", str(e))
finally:
    print("TEST END")
