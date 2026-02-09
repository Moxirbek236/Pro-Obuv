# Render Deployment with Keep-Alive Solution

## 🚀 Render Serverda 15 daqiqadan so'ng uxlab qolish muammosi

### 📋 Muammo:
- Render server 15 daqiqadan so'ng uxlab qoladi
- Bot jarayoni to'xtatiladi
- Qayta ishga tushirish kerak

## 🛠️ Yechimlar:

### 1. **Health Check Endpoint** (Asosiy yechim)
```python
# telegram_bot.py ga qo'shing
@app.route('/keep-alive')
def keep_alive():
    return {"status": "active", "timestamp": datetime.now().isoformat()}

# Har 2 daqiqada o'zi chaqiriladi
```

### 2. **Cron Job** (Render uchun)
```yaml
# render.yaml
services:
  type: web
  env: python
  plan: free
  buildCommand: "pip install -r requirements.txt"
  startCommand: "python telegram_bot.py"
  healthCheckPath: "/health"
  healthCheckTimeout: 100
  restartPolicyType: on_failure
  autoDeploy: false
  
  # Cron job for keep-alive
  cron:
    - url: "/keep-alive"
      schedule: "*/2 * * * *"  # Har 2 daqiqada
```

### 3. **External Ping Service** (Bepul)
```python
# Yangi fayl: ping_service.py
import requests
import time
import os

def ping_render():
    app_url = os.environ.get('RENDER_APP_URL', 'https://your-app.onrender.com')
    
    while True:
        try:
            response = requests.get(f"{app_url}/health", timeout=10)
            print(f"✅ Ping: {response.status_code}")
        except Exception as e:
            print(f"❌ Ping failed: {e}")
        
        time.sleep(120)  # 2 daqiqada

if __name__ == "__main__":
    ping_render()
```

### 4. **Ulanishni saqlash** (Bot ichida)
```python
# telegram_bot.py ga qo'shing
import threading
import time

def keep_connection_alive():
    def ping_thread():
        while True:
            try:
                # O'ziga ping yuborish
                bot.get_me()
                print("✅ Self-ping successful")
            except:
                print("❌ Self-ping failed")
            
            time.sleep(300)  # 5 daqiqada
    
    thread = threading.Thread(target=ping_thread, daemon=True)
    thread.start()
```

## 🚀 Render uchun to'liq yechim:

### 1. **render.yaml faylini yarating:**
```yaml
services:
  type: web
  name: telegram-uzum-bot
  env: python
  plan: free
  buildCommand: "pip install -r requirements.txt"
  startCommand: "python telegram_bot.py"
  healthCheckPath: "/health"
  healthCheckTimeout: 100
  restartPolicyType: on_failure
  autoDeploy: false
  
  # Keep-alive cron job
  cron:
    - url: "/keep-alive"
      schedule: "*/2 * * * *"
      method: GET
```

### 2. **Bot kodiga keep-alive qo'shing:**
<tool_call>write_to_file
<arg_key>CodeContent</arg_key>
<arg_value># Keep-alive endpoint qo'shish uchun
# telegram_bot.py dagi @app.route('/health') dan keyin qo'shing

@app.route('/keep-alive')
def keep_alive():
    """Render serverini tirik saqlash uchun"""
    return {
        "status": "active", 
        "service": "telegram-bot",
        "timestamp": datetime.now().isoformat(),
        "uptime": "Bot is running and processing messages"
    }

@app.route('/ping-self')
def ping_self():
    """Botni o'ziga ping qilish"""
    try:
        # Botni o'ziga tekshirish
        if 'app' in globals() and app:
            bot_info = app.bot.get_me()
            return {
                "status": "success",
                "bot_name": bot_info.username,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
