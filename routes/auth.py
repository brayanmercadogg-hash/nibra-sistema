from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import get_db
from utils.helpers import validate_password

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Por favor ingrese usuario y contrasena', 'error')
            return render_template('auth/login.html')

        db = get_db()
        user = db.execute(
            "SELECT * FROM usuarios WHERE username = ? AND estado = 'ACTIVO'",
            (username,)
        ).fetchone()
        db.close()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Usuario o contrasena incorrectos', 'error')
            return render_template('auth/login.html')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['nombre'] = user['nombre']
        session['rol'] = user['rol']

        if user['debe_cambiar_contrasena']:
            session['force_change'] = True
            flash('Debe cambiar su contrasena por defecto', 'warning')
            return redirect(url_for('auth.change_password'))

        flash('Bienvenido al sistema NIBRA', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html')


@auth.route('/logout')
def logout():
    session.clear()
    flash('Sesion cerrada correctamente', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/cambiar-contrasena', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        actual = request.form.get('actual', '')
        nueva = request.form.get('nueva', '')
        confirmar = request.form.get('confirmar', '')

        if not actual or not nueva or not confirmar:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('auth/cambiar_contrasena.html')

        if nueva != confirmar:
            flash('Las contrasenas nuevas no coinciden', 'error')
            return render_template('auth/cambiar_contrasena.html')

        db = get_db()
        user = db.execute(
            "SELECT * FROM usuarios WHERE id = ?", (session['user_id'],)
        ).fetchone()

        if not user or not check_password_hash(user['password_hash'], actual):
            flash('La contrasena actual es incorrecta', 'error')
            db.close()
            return render_template('auth/cambiar_contrasena.html')

        pwd_errors = validate_password(nueva)
        if pwd_errors:
            flash('Contraseña insegura: ' + '; '.join(pwd_errors), 'error')
            db.close()
            return render_template('auth/cambiar_contrasena.html')

        db.execute(
            "UPDATE usuarios SET password_hash = ?, debe_cambiar_contrasena = 0 WHERE id = ?",
            (generate_password_hash(nueva), session['user_id'])
        )
        db.commit()
        db.close()

        session.pop('force_change', None)
        flash('Contrasena actualizada correctamente', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/cambiar_contrasena.html')
