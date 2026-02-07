import os, sys, traceback

project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
os.environ["SKIP_DB_INIT"] = "1"
print("STARTING IMPORT")
try:
    import app

    print("IMPORTED app")
except Exception:
    traceback.print_exc()
print("DONE")
