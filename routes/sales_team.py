from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db
from utils.decorators import login_required, admin_required

sales_team = Blueprint('sales_team', __name__, url_prefix='/equipo-ventas')


@sales_team.route('/vendedores')
@login_required
def vendedores():
    db = get_db()
    vendedores = db.execute("SELECT * FROM vendedores ORDER BY nombre").fetchall()
    return render_template('sales_team/vendedores.html', vendedores=vendedores)


@sales_team.route('/vendedores', methods=['POST'])
@login_required
def vendedor_crear():
    db = get_db()
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    porcentaje_comision = request.form.get('porcentaje_comision', 0)
    estado = request.form.get('estado', 'ACTIVO')
    usuario_id = request.form.get('usuario_id')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('sales_team.vendedores'))

    try:
        porcentaje_comision = float(porcentaje_comision)
    except ValueError:
        porcentaje_comision = 0

    db.execute(
        "INSERT INTO vendedores (nombre, email, telefono, porcentaje_comision, estado, usuario_id) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre, email, telefono, porcentaje_comision, estado, int(usuario_id) if usuario_id else None)
    )
    db.commit()
    flash('Vendedor registrado correctamente', 'success')
    return redirect(url_for('sales_team.vendedores'))


@sales_team.route('/vendedores/editar/<int:id>')
@login_required
def vendedor_editar(id):
    db = get_db()
    vendedor = db.execute("SELECT * FROM vendedores WHERE id = ?", (id,)).fetchone()
    if not vendedor:
        flash('Vendedor no encontrado', 'error')
        return redirect(url_for('sales_team.vendedores'))
    vendedores = db.execute("SELECT * FROM vendedores ORDER BY nombre").fetchall()
    usuarios = db.execute("SELECT id, nombre, username FROM usuarios ORDER BY nombre").fetchall()
    return render_template('sales_team/vendedores.html', vendedores=vendedores, editing=vendedor, usuarios=usuarios)


@sales_team.route('/vendedores/editar/<int:id>', methods=['POST'])
@login_required
def vendedor_update(id):
    db = get_db()
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    porcentaje_comision = request.form.get('porcentaje_comision', 0)
    estado = request.form.get('estado', 'ACTIVO')
    usuario_id = request.form.get('usuario_id')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('sales_team.vendedores'))

    try:
        porcentaje_comision = float(porcentaje_comision)
    except ValueError:
        porcentaje_comision = 0

    db.execute(
        "UPDATE vendedores SET nombre=?, email=?, telefono=?, porcentaje_comision=?, estado=?, usuario_id=? WHERE id=?",
        (nombre, email, telefono, porcentaje_comision, estado, int(usuario_id) if usuario_id else None, id)
    )
    db.commit()
    flash('Vendedor actualizado correctamente', 'success')
    return redirect(url_for('sales_team.vendedores'))


@sales_team.route('/vendedores/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def vendedor_eliminar(id):
    db = get_db()
    vendedor = db.execute("SELECT * FROM vendedores WHERE id = ?", (id,)).fetchone()
    if not vendedor:
        flash('Vendedor no encontrado', 'error')
    else:
        db.execute("DELETE FROM vendedores WHERE id = ?", (id,))
        db.commit()
        flash('Vendedor eliminado correctamente', 'success')
    db.close()
    return redirect(url_for('sales_team.vendedores'))


@sales_team.route('/comisiones')
@login_required
def comisiones():
    db = get_db()
    vendedor_id = request.args.get('vendedor_id', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')

    query = """
        SELECT v.id, v.nombre, v.porcentaje_comision,
               COUNT(ven.id) AS ventas_count,
               COALESCE(SUM(ven.total), 0) AS total_vendido,
               COALESCE(SUM(ven.total * v.porcentaje_comision / 100), 0) AS comision_generada
        FROM vendedores v
        LEFT JOIN ventas ven ON ven.vendedor_id = v.id
    """
    params = []
    conditions = []

    if vendedor_id:
        conditions.append("v.id = ?")
        params.append(int(vendedor_id))
    if fecha_inicio:
        conditions.append("ven.fecha >= ?")
        params.append(fecha_inicio)
    if fecha_fin:
        conditions.append("ven.fecha <= ?")
        params.append(fecha_fin)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY v.id, v.nombre, v.porcentaje_comision ORDER BY v.nombre"

    resumen = db.execute(query, params).fetchall()

    comisiones_pagadas = db.execute(
        "SELECT vendedor_id, COALESCE(SUM(monto), 0) AS total_pagado FROM comisiones WHERE pagado = 1 GROUP BY vendedor_id"
    ).fetchall()
    pagadas_map = {r['vendedor_id']: r['total_pagado'] for r in comisiones_pagadas}

    comisiones_list = []
    for r in resumen:
        pagado = pagadas_map.get(r['id'], 0)
        comisiones_list.append({
            'vendedor_id': r['id'],
            'vendedor_nombre': r['nombre'],
            'porcentaje_comision': r['porcentaje_comision'],
            'ventas_count': r['ventas_count'],
            'total_vendido': r['total_vendido'],
            'comision_generada': r['comision_generada'],
            'comision_pagada': pagado,
            'comision_pendiente': r['comision_generada'] - pagado,
        })

    vendedores = db.execute("SELECT id, nombre FROM vendedores ORDER BY nombre").fetchall()
    return render_template('sales_team/comisiones.html', comisiones=comisiones_list, vendedores=vendedores, vendedor_id=vendedor_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@sales_team.route('/comisiones/pagar/<int:comision_id>', methods=['POST'])
@login_required
def comision_pagar(comision_id):
    db = get_db()
    resumen_id = request.form.get('vendedor_id')
    fecha_inicio = request.form.get('fecha_inicio', '')
    fecha_fin = request.form.get('fecha_fin', '')

    vendedor = db.execute(
        "SELECT v.id, v.porcentaje_comision FROM vendedores v WHERE v.id = (SELECT vendedor_id FROM ventas WHERE vendedor_id = (SELECT vendedor_id FROM comisiones WHERE id = ?) LIMIT 1)",
        (comision_id,)
    ).fetchone()

    if not vendedor:
        vendedor_id_param = request.form.get('vendedor_id_filter', '')
        if vendedor_id_param:
            vendedor = db.execute("SELECT id, porcentaje_comision FROM vendedores WHERE id = ?", (int(vendedor_id_param),)).fetchone()

    if not vendedor:
        flash('Vendedor no encontrado', 'error')
        return redirect(url_for('sales_team.comisiones'))

    vendedor_id_val = vendedor['id']
    porcentaje = vendedor['porcentaje_comision']

    query_total = "SELECT COALESCE(SUM(total), 0) AS total FROM ventas WHERE vendedor_id = ?"
    params_total = [vendedor_id_val]

    if fecha_inicio:
        query_total += " AND fecha >= ?"
        params_total.append(fecha_inicio)
    if fecha_fin:
        query_total += " AND fecha <= ?"
        params_total.append(fecha_fin)

    total_ventas = db.execute(query_total, params_total).fetchone()['total']
    comision_total = float(total_ventas) * float(porcentaje) / 100

    query_pagado = "SELECT COALESCE(SUM(monto), 0) AS pagado FROM comisiones WHERE vendedor_id = ? AND pagado = 1"
    params_pagado = [vendedor_id_val]
    if fecha_inicio:
        query_pagado += " AND created_at >= ?"
        params_pagado.append(fecha_inicio)
    if fecha_fin:
        query_pagado += " AND created_at <= ?"
        params_pagado.append(fecha_fin)

    comision_pagada = db.execute(query_pagado, params_pagado).fetchone()['pagado']
    pendiente = comision_total - float(comision_pagada)

    if pendiente <= 0:
        flash('No hay comisiones pendientes para este vendedor', 'error')
        return redirect(url_for('sales_team.comisiones', vendedor_id=resumen_id or '', fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))

    db.execute(
        "INSERT INTO comisiones (vendedor_id, porcentaje, monto, pagado, pendiente) VALUES (?, ?, ?, ?, ?)",
        (vendedor_id_val, porcentaje, pendiente, 1, 0)
    )
    db.commit()
    flash(f'Comision de ${pendiente:,.2f} marcada como pagada', 'success')

    return redirect(url_for('sales_team.comisiones', vendedor_id=resumen_id or '', fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))
