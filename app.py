import os
import secrets
from flask import Flask, redirect, url_for, session, render_template, send_from_directory, request, g
from flask_wtf.csrf import CSRFProtect
from config import Config
from database.db import init_db, seed_admin, get_db

app = Flask(__name__)
app.config.from_object(Config)

if app.config.get('SECRET_KEY', '') == 'nibra-erp-secret-key-change-in-production':
    app.config['SECRET_KEY'] = secrets.token_hex(32)

try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except OSError:
    import tempfile
    app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

csrf = CSRFProtect(app)

csrf.exempt('public.catalogo')
csrf.exempt('reports_bp.exportar')
csrf.exempt('auth.change_password')


@app.before_request
def enforce_password_change():
    if session.get('force_change') and request.endpoint not in ('auth.change_password', 'auth.logout', 'static'):
        return redirect(url_for('auth.change_password'))


@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Evita que el navegador muestre versiones viejas de las paginas tras un deploy
    ctype = response.headers.get('Content-Type', '')
    if ctype.startswith('text/html'):
        response.headers['Cache-Control'] = 'no-store, must-revalidate'
    return response


@app.errorhandler(413)
def request_entity_too_large(e):
    return render_template('errors/500.html'), 413


from routes.auth import auth
from routes.main import main
from routes.inventory import inventory_bp
from routes.contacts import contacts
from routes.transactions import transactions
from routes.finance import finance
from routes.partners import partners_bp
from routes.sales_team import sales_team
from routes.reports import reports_bp
from routes.public import public_bp
from routes.solicitudes import solicitudes_bp

app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(inventory_bp)
app.register_blueprint(contacts)
app.register_blueprint(transactions)
app.register_blueprint(finance)
app.register_blueprint(partners_bp)
app.register_blueprint(sales_team)
app.register_blueprint(reports_bp)
app.register_blueprint(public_bp)
app.register_blueprint(solicitudes_bp)


@app.route('/redirect-to-catalog')
def redirect_to_catalog():
    return redirect(url_for('public.catalogo'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'),
        'favicon.ico',
        mimetype='image/x-icon'
    )


@app.template_filter('currency')
def currency_filter(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@app.context_processor
def inject_user():
    ctx = {
        'current_user': {
            'id': session.get('user_id'),
            'nombre': session.get('nombre'),
            'rol': session.get('rol')
        } if 'user_id' in session else None
    }
    if session.get('rol') == 'ADMIN':
        try:
            db = get_db()
            row = db.execute(
                "SELECT COUNT(*) AS cnt FROM solicitudes_productos WHERE estado = 'PENDIENTE'"
            ).fetchone()
            db.close()
            ctx['solicitudes_pendientes'] = row['cnt'] if row else 0
        except Exception:
            ctx['solicitudes_pendientes'] = 0
    return ctx


@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


_db_initialized = False

@app.before_request
def ensure_db():
    global _db_initialized
    if not _db_initialized:
        try:
            init_db()
            seed_admin()
            _db_initialized = True
        except Exception as e:
            import traceback
            print(f"WARNING: DB init failed: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
