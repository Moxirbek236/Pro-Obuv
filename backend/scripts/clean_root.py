import os
import shutil
import glob

def move_item(src, dst_dir):
    if not os.path.exists(src):
        return
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    dst = os.path.join(dst_dir, os.path.basename(src))
    print(f"Moving {src} -> {dst}")
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"Failed to move {src}: {e}")

def main():
    root = os.getcwd()
    backend = os.path.join(root, 'backend')
    frontend = os.path.join(root, 'frontend')
    
    # Define explicit moves based on user request to clean root
    
    # 1. Database -> backend/database
    move_item('database', backend)
    
    # 2. Docs -> backend/docs
    move_item('docs', backend)
    
    # 3. Scripts -> backend/scripts
    move_item('scripts', backend)
    
    # 4. Tests -> backend/tests
    move_item('tests', backend)
    
    # 5. Tools -> backend/tools
    move_item('tools', backend)
    
    # 6. Instance -> backend/instance (flask instance folder)
    move_item('instance', backend)
    
    # 7. Attached Assets -> backend/attached_assets
    move_item('attached_assets', backend)
    
    # 8. Requirements & Env
    move_item('requirements.txt', backend)
    for f in glob.glob('.env*'):
        move_item(f, backend)
        
    # 9. Logs
    logs_dir = os.path.join(backend, 'logs')
    for f in glob.glob('*.log'):
        move_item(f, logs_dir)
        
    # 10. Sitemap & App.js -> Frontend? or Backend static?
    # Sitemap is usually served from static or root. Let's put in frontend/static
    move_item('sitemap.xml', os.path.join(frontend, 'static'))
    
    # App.js typically part of frontend assets
    for f in glob.glob('app.js*'):
        move_item(f, os.path.join(frontend, 'static', 'js')) # Create js folder if needed

    # 11. Tmp files
    tmp_dir = os.path.join(backend, 'tmp')
    for f in glob.glob('tmp_qr*'):
        move_item(f, tmp_dir)
        
    # 12. List tables script and other loose python files
    # move_files.py, list_tables.py -> backend/scripts
    move_item('list_tables.py', os.path.join(backend, 'scripts'))
    # Don't move move_files.py yet (we might be running it? No, this is clean_root.py)
    # move_item('move_files.py', os.path.join(backend, 'scripts')) 
    
    # 13. Replit/Config files to backend to hide them
    for f in glob.glob('.replit*'):
        move_item(f, backend)
    move_item('.python-version', backend)
    
    # Clean up 'New folder' if empty or irrelevant
    move_item('New folder', os.path.join(backend, 'misc'))

if __name__ == '__main__':
    main()
