from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.db import get_db
from utils.decorators import login_required, admin_required, partner_or_admin_required

solicitudes_bp = Blueprint('solicitudes', __name__, url_prefix='/solicitudes')

ESTADOS = ('PENDIENTE', 'ATENDIDA', 'RECHAZADA')


def _vendedor_del_usuario(db, user_id):
    return db.execute(
        "SELECT * FROM vendedores WHERE usuario_id = ? LIMIT 1", (user_id,)
    ).fetchone()


@solicitudes_bp.route('/')
@login_required
def index():
    """Vendedores ven sus solicitudes; admin es redirigido a la bandeja."""
    from flask import session
    if session.get('rol') == 'ADMIN':
        return redirect(url_for('solicitudes.bandeja'))
    return redirect(url_for('solicitudes.mis'))


@solicitudes_bp.route('/mis')
@login_required
def mis():
    db = get_db()
    vend = _vendedor_del_usuario(db, session['user_id'])
    lista = []
    if vend:
        lista = db.execute(
            '''SELECT s.*, v.nombre as vendedor_nombre
               FROM solicitudes_productos s
               LEFT JOIN vendedores v ON s.vendedor_id = v.id
               WHERE s.vendedor_id = ?
               ORDER BY s.created_at DESC''',
            (vend['id'],)
        ).fetchall()
    db.close()
    return render_template('solicitudes/mis_solicitudes.html', solicitudes=lista, vendedor=vend)


@solicitudes_bp.route('/crear', methods=['POST'])
@login_required
def crear():
    nombre = request.form.get('nombre_producto', '').strip()
    detalles = request.form.get('detalles', '').strip()
    try:
        cantidad = max(1, int(request.form.get('cantidad', 1)))
    except (ValueError, TypeError):
        cantidad = 1

    if not nombre:
        flash('El nombre del producto es obligatorio', 'error')
        return redirect(url_for('solicitudes.mis'))

    db = get_db()
    vend = _vendedor_del_usuario(db, session['user_id'])
    try:
        db.execute(
            '''INSERT INTO solicitudes_productos (vendedor_id, usuario_id, nombre_producto, detalles, cantidad)
               VALUES (?, ?, ?, ?, ?)''',
            (vend['id'] if vend else None, session['user_id'], nombre, detalles, cantidad)
        )
        db.commit()
        flash('Solicitud enviada correctamente. El administrador la revisará pronto.', 'success')
    except Exception as e:
        print(f"ERROR crear solicitud: {e}")
        flash('Error al enviar la solicitud', 'error')
    finally:
        db.close()
    return redirect(url_for('solicitudes.mis'))


@solicitudes_bp.route('/cancelar/<int:id>', methods=['POST'])
@login_required
def cancelar(id):
    """El vendedor puede cancelar una solicitud propia mientras este PENDIENTE."""
    db = get_db()
    try:
        row = db.execute("SELECT id, estado FROM solicitudes_productos WHERE id = ?", (id,)).fetchone()
        if not row:
            flash('Solicitud no encontrada', 'error')
        elif row['estado'] != 'PENDIENTE':
            flash('Solo se pueden cancelar solicitudes pendientes', 'error')
        else:
            db.execute("DELETE FROM solicitudes_productos WHERE id = ?", (id,))
            db.commit()
            flash('Solicitud cancelada', 'success')
    except Exception as e:
        print(f"ERROR cancelar solicitud: {e}")
        flash('Error al cancelar la solicitud', 'error')
    finally:
        db.close()
    return redirect(url_for('solicitudes.mis'))


@solicitudes_bp.route('/bandeja')
@partner_or_admin_required
def bandeja():
    filtro = request.args.get('estado', '').strip()
    if filtro not in ESTADOS:
        filtro = ''
    db = get_db()
    query = '''
        SELECT s.*, v.nombre as vendedor_nombre, u.username
        FROM solicitudes_productos s
        LEFT JOIN vendedores v ON s.vendedor_id = v.id
        LEFT JOIN usuarios u ON s.usuario_id = u.id
    '''
    params = []
    if filtro:
        query += ' WHERE s.estado = ?'
        params.append(filtro)
    # pendientes primero, luego las mas recientes
    query += " ORDER BY CASE s.estado WHEN 'PENDIENTE' THEN 0 ELSE 1 END, s.created_at DESC"
    lista = db.execute(query, params).fetchall()
    counts = {e: 0 for e in ESTADOS}
    for row in db.execute("SELECT estado, COUNT(*) AS cnt FROM solicitudes_productos GROUP BY estado").fetchall():
        counts[row['estado']] = row['cnt']
    db.close()
    return render_template(
        'solicitudes/bandeja.html',
        solicitudes=lista,
        filtro=filtro,
        counts=counts,
        estados=ESTADOS
    )


@solicitudes_bp.route('/atender/<int:id>', methods=['POST'])
@admin_required
def atender(id):
    respuesta = request.form.get('respuesta', '').strip()
    db = get_db()
    try:
        cur = db.execute(
            "UPDATE solicitudes_productos SET estado = 'ATENDIDA', respuesta = ? WHERE id = ?",
            (respuesta or None, id)
        )
        if cur.rowcount == 0:
            flash('Solicitud no encontrada', 'error')
        else:
            db.commit()
            flash('Solicitud marcada como atendida', 'success')
    finally:
        db.close()
    return redirect(url_for('solicitudes.bandeja'))


@solicitudes_bp.route('/rechazar/<int:id>', methods=['POST'])
@admin_required
def rechazar(id):
    respuesta = request.form.get('respuesta', '').strip()
    db = get_db()
    try:
        cur = db.execute(
            "UPDATE solicitudes_productos SET estado = 'RECHAZADA', respuesta = ? WHERE id = ?",
            (respuesta or None, id)
        )
        if cur.rowcount == 0:
            flash('Solicitud no encontrada', 'error')
        else:
            db.commit()
            flash('Solicitud rechazada', 'success')
    finally:
        db.close()
    return redirect(url_for('solicitudes.bandeja'))


@solicitudes_bp.route('/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar(id):
    db = get_db()
    try:
        db.execute("DELETE FROM solicitudes_productos WHERE id = ?", (id,))
        db.commit()
        flash('Solicitud eliminada', 'success')
    except Exception as e:
        print(f"ERROR eliminar solicitud: {e}")
        flash('Error al eliminar la solicitud', 'error')
    finally:
        db.close()
    return redirect(url_for('solicitudes.bandeja'))
