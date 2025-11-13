from flask import Blueprint, render_template, session, g, redirect, request, abort
from flask import url_for


def register_i18n(app):
    """Register lightweight i18n routes.

    This creates these routes:
      - / -> redirects to default language (e.g. /uz/)
      - /<lang>/ -> sets interface language and renders index
      - /<lang>/<path:page> -> sets interface language and attempts to render template

    It intentionally keeps things small and non-invasive: it does not try to
    rewrite or re-register all existing application routes under a language
    prefix. Instead it provides a simple, discoverable entrypoint so visiting
    '/ru/' or '/en/' will immediately set the UI language and show the main
    page. Teams can progressively add more language-prefixed routes if they
    want full parity.
    """

    bp = Blueprint("i18n", __name__, template_folder="templates")

    @bp.route("/")
    def root_redirect():
        # redirect bare root to the configured default language root
        default = app.config.get("DEFAULT_LANGUAGE", "ru")
        return redirect(f"/{default}/menu")

    @bp.route("/<lang>/")
    def lang_index(lang):
        if lang not in app.config.get("SUPPORTED_LANGUAGES", ["uz", "ru", "en", "kz"]):
            abort(404)
        # persist chosen language in session and request-global g
        try:
            session["interface_language"] = lang
        except Exception:
            pass
        try:
            g.interface_language = lang
        except Exception:
            pass
        # Render the public menu as the site homepage for language roots
        try:
            return render_template("menu.html")
        except Exception:
            # Fallback simple response if template not renderable
            return f"<html><body><h1>Site ({lang})</h1><p>Language set to {lang}.</p></body></html>"

    @bp.route("/<lang>/<path:page>")
    def lang_page(lang, page):
        if lang not in app.config.get("SUPPORTED_LANGUAGES", ["uz", "ru", "en", "kz"]):
            abort(404)
        try:
            session["interface_language"] = lang
        except Exception:
            pass
        try:
            g.interface_language = lang
        except Exception:
            pass
        # Special-case known dynamic routes that need server-side context
        if page == "menu":
            # Let the existing /menu view build the context (it reads session['interface_language']).
            try:
                return redirect(url_for("menu"))
            except Exception:
                return render_template("menu.html")

        # Try to render a template that matches the page path (e.g. '/ru/about' -> 'about.html')
        tmpl_name = f"{page}.html"
        try:
            return render_template(tmpl_name)
        except Exception:
            # If template not found, fall back to a 404 page using existing error template
            try:
                return render_template("error.html", error_code=404, error_message="Sahifa topilmadi"), 404
            except Exception:
                abort(404)

    app.register_blueprint(bp)
