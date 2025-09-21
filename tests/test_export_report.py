# Simple test for export report endpoint using Flask test client
import os
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports when running from tests folder
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Prevent heavy DB init during import in app
os.environ["SKIP_DB_INIT"] = "1"

from app import app


def run_test():
    client = app.test_client()
    sample = {
        "summary": {
            "total_orders": 10,
            "total_revenue": 250000,
            "avg_check": 25000,
            "new_customers": 2,
            "growth_rate": 5.0,
        },
        "sales": [
            {"date": "2025-09-01", "orders_count": 5, "revenue": 120000},
            {"date": "2025-09-02", "orders_count": 5, "revenue": 130000},
        ],
        "products": [{"name": "Lavash", "sold": 20, "revenue": 100000}],
        "customers": [{"id": 1, "name": "Ali"}],
        "staff": [{"id": 2, "name": "Olim"}],
        "branches": [
            {"id": 1, "name": "Bosh filial", "orders_count": 10, "revenue": 250000}
        ],
    }

    resp = client.post("/api/super-admin/export-report", json=sample)
    print("Status code:", resp.status_code)
    print("Content-Type:", resp.content_type)
    data = resp.data
    print("Payload size:", len(data))
    # write to disk for manual inspection
    with open("tests/output_report_test.xlsx", "wb") as f:
        f.write(data)
    print("Wrote tests/output_report_test.xlsx")


if __name__ == "__main__":
    run_test()
