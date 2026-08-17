from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db
from utils.decorators import login_required, admin_required

partners_bp = Blueprint('partners', __name__, url_prefix='/socios')


@partners_bp.route('/lista', methods=['GET', 'POST'])
@login_required
def socios():
    db = get_db()
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        porcentaje = float(request.form.get('porcentaje', 0))
        capital_aportado = float(request.form.get('capital_aportado', 0))
        fecha_ingreso = request.form.get('fecha_ingreso')
        estado = request.form.get('estado', 'ACTIVO')

        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('partners.socios'))

        total = db.execute('SELECT COALESCE(SUM(porcentaje), 0) as total FROM socios').fetchone()['total']
        if total + porcentaje > 100:
            flash('La suma de porcentajes no puede exceder 100%', 'error')
            return redirect(url_for('partners.socios'))

        db.execute(
            'INSERT INTO socios (nombre, porcentaje, capital_aportado, fecha_ingreso, estado) VALUES (?, ?, ?, ?, ?)',
            (nombre, porcentaje, capital_aportado, fecha_ingreso, estado)
        )
        db.commit()
        db.close()
        flash('Socio registrado exitosamente', 'success')
        return redirect(url_for('partners.socios'))

    socios_list = db.execute('SELECT * FROM socios ORDER BY nombre').fetchall()
    db.close()
    return render_template('partners/socios.html', socios=socios_list)


@partners_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_socio(id):
    db = get_db()
    socio = db.execute('SELECT * FROM socios WHERE id = ?', (id,)).fetchone()
    if not socio:
        flash('Socio no encontrado', 'error')
        return redirect(url_for('partners.socios'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        porcentaje = float(request.form.get('porcentaje', 0))
        capital_aportado = float(request.form.get('capital_aportado', 0))
        fecha_ingreso = request.form.get('fecha_ingreso')
        estado = request.form.get('estado', 'ACTIVO')

        if not nombre:
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('partners.socios'))

        total = db.execute('SELECT COALESCE(SUM(porcentaje), 0) as total FROM socios WHERE id != ?', (id,)).fetchone()['total']
        if total + porcentaje > 100:
            flash('La suma de porcentajes no puede exceder 100%', 'error')
            return redirect(url_for('partners.socios'))

        db.execute(
            'UPDATE socios SET nombre=?, porcentaje=?, capital_aportado=?, fecha_ingreso=?, estado=? WHERE id=?',
            (nombre, porcentaje, capital_aportado, fecha_ingreso, estado, id)
        )
        db.commit()
        db.close()
        flash('Socio actualizado exitosamente', 'success')
        return redirect(url_for('partners.socios'))

    socios_list = db.execute('SELECT * FROM socios ORDER BY nombre').fetchall()
    db.close()
    return render_template('partners/socios.html', socios=socios_list, editing=socio)


@partners_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_socio(id):
    db = get_db()
    db.execute('DELETE FROM socios WHERE id = ?', (id,))
    db.commit()
    db.close()
    flash('Socio eliminado exitosamente', 'success')
    return redirect(url_for('partners.socios'))


@partners_bp.route('/distribucion')
@login_required
def distribucion():
    db = get_db()
    distribuciones = db.execute('SELECT * FROM distribuciones ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('partners/distribucion.html', distribuciones=distribuciones)


@partners_bp.route('/calcular', methods=['POST'])
@login_required
def calcular_distribucion():
    db = get_db()
    periodo_inicio = request.form.get('periodo_inicio')
    periodo_fin = request.form.get('periodo_fin')

    total_ingresos = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM ingresos WHERE fecha BETWEEN ? AND ?",
        (periodo_inicio, periodo_fin)
    ).fetchone()['total']
    total_compras = db.execute(
        "SELECT COALESCE(SUM(total), 0) as total FROM compras WHERE fecha BETWEEN ? AND ?",
        (periodo_inicio, periodo_fin)
    ).fetchone()['total']
    total_gastos = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM gastos WHERE fecha BETWEEN ? AND ?",
        (periodo_inicio, periodo_fin)
    ).fetchone()['total']
    utilidad_neta = float(total_ingresos) - float(total_compras) - float(total_gastos)

    cursor = db.execute(
        'INSERT INTO distribuciones (periodo_inicio, periodo_fin, utilidad_neta, estado) VALUES (?, ?, ?, ?)',
        (periodo_inicio, periodo_fin, utilidad_neta, 'PENDIENTE')
    )
    distribucion_id = cursor.lastrowid

    socios_list = db.execute("SELECT * FROM socios WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    for socio in socios_list:
        monto = utilidad_neta * (float(socio['porcentaje']) / 100)
        db.execute(
            'INSERT INTO distribucion_detalles (distribucion_id, socio_id, porcentaje, monto) VALUES (?, ?, ?, ?)',
            (distribucion_id, socio['id'], socio['porcentaje'], monto)
        )

    db.commit()
    db.close()
    flash(f'Distribucion calculada. Utilidad neta: {utilidad_neta:,.2f}', 'success')
    return redirect(url_for('partners.distribucion'))


@partners_bp.route('/registrar-pago/<int:distribucion_id>', methods=['POST'])
@login_required
def registrar_pago(distribucion_id):
    db = get_db()
    dist = db.execute('SELECT * FROM distribuciones WHERE id = ?', (distribucion_id,)).fetchone()
    if not dist:
        flash('Distribucion no encontrada', 'error')
    else:
        from datetime import date
        db.execute(
            "UPDATE distribuciones SET estado = 'PAGADA', fecha_distribucion = ? WHERE id = ?",
            (date.today().isoformat(), distribucion_id)
        )
        db.execute(
            "UPDATE distribucion_detalles SET pagado = monto WHERE distribucion_id = ?",
            (distribucion_id,)
        )
        db.commit()
        flash('Pago registrado exitosamente', 'success')
    db.close()
    return redirect(url_for('partners.distribucion'))
