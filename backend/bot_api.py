# ===== BOT API ENDPOINTS =====

@app.route('/api/bot/register-user', methods=['POST'])
def api_bot_register_user():
    """Register a bot user"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        name = data.get('name', 'User')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id required'}), 400
        
        execute_query("""
            INSERT INTO bot_users (user_id, name, created_at, last_active)
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE SET last_active = NOW(), name = EXCLUDED.name
        """, (str(user_id), name))
        
        return jsonify({'success': True})
    except Exception as e:
        app_logger.error(f"Bot register user error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/categories', methods=['GET'])
def api_bot_categories():
    """Get product categories for bot"""
    try:
        # Get distinct categories from menu_items
        rows = execute_query("""
            SELECT DISTINCT category as name, category as id 
            FROM menu_items 
            WHERE category IS NOT NULL AND category != ''
            ORDER BY category
        """, fetch_all=True) or []
        
        categories = [{'name': r['name'], 'id': r['id']} for r in rows]
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        app_logger.error(f"Bot categories error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/products', methods=['GET'])
def api_bot_products():
    """Get products for bot"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 10))
        
        query = "SELECT id, name, description, price, image FROM menu_items WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY id DESC LIMIT %s"
        params.append(limit)
        
        rows = execute_query(query, tuple(params), fetch_all=True) or []
        
        products = []
        for r in rows:
            products.append({
                'id': r['id'],
                'name': r['name'],
                'description': r.get('description', ''),
                'price': float(r.get('price', 0)),
                'image': get_cloudinary_url(r.get('image')) if r.get('image') else None
            })
        
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        app_logger.error(f"Bot products error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/uzum/products', methods=['GET'])
def api_bot_uzum_products():
    """Get Uzum Market products for bot"""
    try:
        # Read from local JSON file
        uzum_file = os.path.join(os.path.dirname(__file__), 'data', 'uzum_products.json')
        
        if not os.path.exists(uzum_file):
            return jsonify({'success': False, 'error': 'Uzum data not found'}), 404
        
        with open(uzum_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        return jsonify({'success': True, 'products': products[:20]})  # Limit to 20
    except Exception as e:
        app_logger.error(f"Bot Uzum products error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/commands/pending', methods=['GET'])
def api_bot_commands_pending():
    """Get pending bot commands"""
    try:
        rows = execute_query("""
            SELECT id, type, payload, status, created_at, processed_at, error 
            FROM bot_commands 
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT 10
        """, fetch_all=True) or []
        
        commands = []
        for r in rows:
            commands.append({
                'id': r['id'],
                'type': r['type'],
                'payload': r['payload'] if isinstance(r['payload'], dict) else json.loads(r['payload'] or '{}'),
                'status': r['status'],
                'created_at': str(r['created_at'])
            })
        
        return jsonify({'success': True, 'commands': commands})
    except Exception as e:
        app_logger.error(f"Bot pending commands error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/commands/<int:cmd_id>/status', methods=['POST'])
def api_bot_command_status(cmd_id):
    """Update bot command status"""
    try:
        data = request.get_json() or {}
        status = data.get('status', 'completed')
        error = data.get('error')
        
        execute_query("""
            UPDATE bot_commands 
            SET status = %s, processed_at = NOW(), error = %s
            WHERE id = %s
        """, (status, error, cmd_id))
        
        return jsonify({'success': True})
    except Exception as e:
        app_logger.error(f"Bot command status update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bot/subscribers', methods=['GET'])
def api_bot_subscribers():
    """Get all bot subscribers"""
    try:
        rows = execute_query("""
            SELECT user_id, name, created_at, last_active 
            FROM bot_users 
            ORDER BY last_active DESC
        """, fetch_all=True) or []
        
        subscribers = []
        for r in rows:
            subscribers.append({
                'user_id': r['user_id'],
                'name': r.get('name', 'User'),
                'created_at': str(r['created_at']),
                'last_active': str(r['last_active'])
            })
        
        return jsonify({'success': True, 'subscribers': subscribers})
    except Exception as e:
        app_logger.error(f"Bot subscribers error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/super-admin/bot/broadcast', methods=['POST'])
def api_super_bot_broadcast():
    """Create a broadcast command for the bot"""
    if not session.get('super_admin'):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    try:
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        photo = data.get('photo', '').strip()
        target = data.get('target', 'all')
        
        if not text:
            return jsonify({'success': False, 'error': 'Text required'}), 400
        
        payload = {
            'text': text,
            'photo': photo if photo else None,
            'target': target
        }
        
        execute_query("""
            INSERT INTO bot_commands (type, payload, status, created_at)
            VALUES (%s, %s, %s, NOW())
        """, ('broadcast', json.dumps(payload), 'pending'))
        
        return jsonify({'success': True, 'message': 'Broadcast queued'})
    except Exception as e:
        app_logger.error(f"Bot broadcast error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/super-admin/bot/history', methods=['GET'])
def api_super_bot_history():
    """Get bot command history"""
    if not session.get('super_admin'):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    
    try:
        limit = int(request.args.get('limit', 20))
        
        rows = execute_query("""
            SELECT id, type, payload, status, created_at, processed_at, error 
            FROM bot_commands 
            ORDER BY id DESC 
            LIMIT %s
        """, (limit,), fetch_all=True) or []
        
        history = []
        for r in rows:
            history.append({
                'id': r['id'],
                'type': r['type'],
                'status': r['status'],
                'created_at': str(r['created_at']),
                'processed_at': str(r['processed_at']) if r.get('processed_at') else None,
                'error': r.get('error')
            })
        
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        app_logger.error(f"Bot history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
