import os
import shutil
import glob

# Config
DIRS = ['frontend', 'backend', 'database', 'scripts', 'docs']
ROOT_FILES_TO_KEEP = ['run_all.py', 'requirements.txt', '.env', '.gitignore', '.git', '.github', '.vscode', '.idea', 'venv', 'move_files.py']

def ensure_dirs():
    for d in DIRS:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created {d}")

def move_path(src, dst_folder):
    if not os.path.exists(src):
        return
    
    dst = os.path.join(dst_folder, os.path.basename(src))
    if os.path.exists(dst):
        print(f"Skipping {src} -> {dst} (Already exists)")
        return
        
    print(f"Moving {src} -> {dst}")
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"Error moving {src}: {e}")

def main():
    ensure_dirs()
    
    # 1. Frontend
    move_path('templates', 'frontend')
    move_path('static', 'frontend')
    move_path('favicons', 'frontend')
    move_path('icons', 'frontend')
    move_path('styles_images', 'frontend')
    move_path('package.json', 'frontend')
    move_path('package-lock.json', 'frontend')
    move_path('node_modules', 'frontend')
    
    # Verification HTMLs - move to frontend/static for now, logic needed to serve them
    for f in glob.glob('google*.html'): move_path(f, 'frontend/static')
    for f in glob.glob('yandex*.html'): move_path(f, 'frontend/static')
    
    # 2. Database
    move_path('database.sqlite3', 'database')
    move_path('database.db', 'database')
    move_path('restaurant.db', 'database')
    for f in glob.glob('database.sqlite3*'): move_path(f, 'database') # wal, shm, bak
    move_path('data', 'backend') # 'data' folder typically contains app data like translations. Better in backend.
    
    # 3. Backend
    BACKEND_FILES = [
        'app.py', 'config.py', 'utils.py', 'cloudinary_helpers.py', 
        'i18n.py', 'location_service.py', 'payment_settings.py', 
        'sms_helper.py', 'routes.json', 'translation.json', 'swagger.yaml', 'swagger_tokens.json'
    ]
    for f in BACKEND_FILES:
        move_path(f, 'backend')
        
    move_path('api', 'backend')
    move_path('services', 'backend')
    move_path('app_module', 'backend')
    
    # 4. Docs
    for f in glob.glob('*.md'):
        if f not in ROOT_FILES_TO_KEEP:
            move_path(f, 'docs')
    for f in glob.glob('*.txt'):
        if f not in ROOT_FILES_TO_KEEP:
            move_path(f, 'docs')
            
    # 5. Scripts (catch-all for .py, .html remaining)
    # We want to keep run_web.py and run_bot.py in scripts maybe, or delete them as replaced by run_all?
    # User said "run_all.py yarat". I will move run_web and run_bot to scripts as examples.
    
    for f in glob.glob('*.py'):
        if f not in ROOT_FILES_TO_KEEP and f not in BACKEND_FILES:
             move_path(f, 'scripts')

    for f in glob.glob('*.html'): # Leftover htmls
        if f not in ROOT_FILES_TO_KEEP and not f.startswith('google') and not f.startswith('yandex'):
             move_path(f, 'scripts') # Testing htmls mostly

    # 6. Logs
    move_path('logs', 'backend') # Logs usually belong to the app running
    move_path('backups', 'database') # Backups belong to DB

if __name__ == '__main__':
    main()
