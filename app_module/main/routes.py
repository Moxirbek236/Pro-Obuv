from app.main import bp
from flask import render_template

@bp.route('/')
def index():
    """Bosh sahifa - menyuga yo'naltirish"""
    from flask import redirect, url_for
    # Asosiy sahifani to'g'ridan-to'g'ri menyuga yo'naltirish
    return redirect('/menu')
