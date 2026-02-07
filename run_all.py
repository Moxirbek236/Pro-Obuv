import os
import subprocess
import sys
import time

def main():
    """
    Universal Launcher for Safety.uz System
    Runs:
      1. Backend (API/Web)
      2. Frontend (Proxy Server)
      3. Telegram Bot
    """
    print(">>> Starting Safety.uz Full System...")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths
    backend_dir = os.path.join(root_dir, 'backend')
    frontend_dir = os.path.join(root_dir, 'frontend')
    
    backend_script = os.path.join(backend_dir, 'app.py')
    frontend_script = os.path.join(frontend_dir, 'server.py')
    bot_script = os.path.join(root_dir, 'bot', 'telegram_bot.py')
    
    # Environment
    env = os.environ.copy()
    env['PYTHONPATH'] = backend_dir + os.pathsep + env.get('PYTHONPATH', '')
    env['START_TELEGRAM_BOT'] = '0'
    
    # Defaults for LOCAL execution
    # When running locally via run_all.py, we almost always want components to talk to each other locally.
    api_url = env.get('BACKEND_URL', 'http://127.0.0.1:5000') 
    
    # Force override for consistency in local dev unless explicitly set
    if 'BACKEND_URL' not in os.environ:
         api_url = 'http://127.0.0.1:5000'

    env['BACKEND_URL'] = api_url # For frontend
    env['FLASK_APP_URL'] = api_url # For bot

    processes = []

    def start_process(name, cmd, cwd, env_vars=None):
        print(f">>> Launching {name}...")
        try:
            p = subprocess.Popen(cmd, cwd=cwd, env=env_vars or env)
            processes.append((name, p))
            return p
        except Exception as e:
            print(f"!!! Failed to start {name}: {e}")
            return None

    try:
        # 1. Start Backend
        # Note: Backend is the reliable source of truth, needs to start first
        start_process("Backend API", [sys.executable, backend_script], backend_dir)
        
        print(">>> Waiting for Backend to be ready...")
        time.sleep(3) 

        # 2. Start Bot
        # Bot needs FLASK_APP_URL, which we set in env above
        # Verify bot script exists
        if os.path.exists(bot_script):
            start_process("Telegram Bot", [sys.executable, bot_script], root_dir)
        else:
            print(">>> Bot script not found, skipping.")

        print(">>> All systems go! Press Ctrl+C to stop.")
        print(f"    - Web Interface: {api_url}")
        
        while True:
            time.sleep(1)
            for name, p in processes:
                if p.poll() is not None:
                    print(f">>> {name} exited unexpectedly code={p.returncode}")
                    # If backend dies, everything is practically dead, but let's just break main loop
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n>>> Shutdown requested.")
    finally:
        print(">>> Terminating processes...")
        for name, p in processes:
            if p.poll() is None:
                print(f"    Stopping {name}...")
                p.terminate()
        print(">>> Shutdown complete.")

if __name__ == '__main__':
    main()
