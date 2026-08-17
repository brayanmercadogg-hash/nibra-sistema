from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.db import get_db, generar_codigo
from utils.decorators import login_required
from datetime import datetime

transactions = Blueprint('transactions', __name__, url_prefix='/transacciones')


@transactions.route('/compras')
@login_required
def compras_list():
    db = get_db()
    compras = db.execute('''
        SELECT c.*, p.nombre as proveedor_nombre
        FROM compras c
        LEFT JOIN proveedores p ON c.proveedor_id = p.id
        ORDER BY c.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('transactions/compras.html', compras=compras)


@transactions.route('/compras/nueva', methods=['GET'])
@login_required
def compra_nueva():
    db = get_db()
    proveedores = db.execute("SELECT * FROM proveedores WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    productos = db.execute("SELECT * FROM productos WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    db.close()
    return render_template('transactions/compra_form.html', compra=None, proveedores=proveedores, productos=productos)


@transactions.route('/compras/nueva', methods=['POST'])
@login_required
def compra_crear():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    proveedor_id = data.get('proveedor_id')
    metodo_pago = data.get('metodo_pago', 'EFECTIVO')
    observaciones = data.get('observaciones', '')
    items = data.get('items', [])
    fecha = datetime.now().strftime('%Y-%m-%d')

    if not items:
        return jsonify({'success': False, 'error': 'Debe agregar al menos un producto'}), 400

    pagado = 0
    try:
        pagado = float(data.get('pagado', 0))
    except (ValueError, TypeError):
        pagado = 0

    total = 0
    processed_items = []
    for item in items:
        try:
            cantidad = float(item.get('cantidad', 1))
            precio_unitario = float(item.get('precio_unitario', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Valores numéricos inválidos'}), 400

        if cantidad <= 0 or precio_unitario < 0:
            return jsonify({'success': False, 'error': 'Cantidad y precio deben ser positivos'}), 400

        subtotal = cantidad * precio_unitario
        total += subtotal
        processed_items.append({
            'producto_id': item.get('producto_id'),
            'nombre_producto': item.get('nombre_producto', ''),
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal': subtotal
        })

    saldo = total - pagado

    db = get_db()
    codigo = generar_codigo(db, 'compras', 'NIB-CMP')
    cursor = db.execute(
        'INSERT INTO compras (codigo, proveedor_id, fecha, total, pagado, saldo, metodo_pago, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (codigo, proveedor_id, fecha, total, pagado, saldo, metodo_pago, observaciones)
    )
    compra_id = cursor.lastrowid

    for item in processed_items:
        db.execute(
            'INSERT INTO compra_detalles (compra_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)',
            (compra_id, item['producto_id'], item['nombre_producto'], item['cantidad'], item['precio_unitario'], item['subtotal'])
        )
        if item['producto_id']:
            db.execute(
                'UPDATE productos SET precio_compra = ? WHERE id = ?',
                (item['precio_unitario'], item['producto_id'])
            )

    db.commit()
    db.close()
    flash(f'Compra registrada exitosamente con código {codigo}', 'success')
    return jsonify({'success': True, 'compra_id': compra_id, 'codigo': codigo})


@transactions.route('/compras/<int:id>')
@login_required
def compra_detalle(id):
    db = get_db()
    compra = db.execute('''
        SELECT c.*, p.nombre as proveedor_nombre
        FROM compras c
        LEFT JOIN proveedores p ON c.proveedor_id = p.id
        WHERE c.id = ?
    ''', (id,)).fetchone()
    detalles = db.execute('''
        SELECT cd.*, pr.codigo as producto_codigo
        FROM compra_detalles cd
        LEFT JOIN productos pr ON cd.producto_id = pr.id
        WHERE cd.compra_id = ?
    ''', (id,)).fetchall()
    db.close()
    if not compra:
        flash('Compra no encontrada', 'danger')
        return redirect(url_for('transactions.compras_list'))
    return render_template('transactions/compra_detalle.html', compra=compra, detalles=detalles)


@transactions.route('/compras/editar/<int:id>', methods=['GET'])
@login_required
def compra_editar_form(id):
    db = get_db()
    compra = db.execute('SELECT * FROM compras WHERE id = ?', (id,)).fetchone()
    if not compra:
        flash('Compra no encontrada', 'danger')
        db.close()
        return redirect(url_for('transactions.compras_list'))
    detalles = db.execute('SELECT * FROM compra_detalles WHERE compra_id = ?', (id,)).fetchall()
    proveedores = db.execute("SELECT * FROM proveedores WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    productos = db.execute("SELECT * FROM productos WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    db.close()
    return render_template('transactions/compra_form.html', compra=compra, detalles=detalles, proveedores=proveedores, productos=productos)


@transactions.route('/compras/editar/<int:id>', methods=['POST'])
@login_required
def compra_editar(id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    proveedor_id = data.get('proveedor_id')
    metodo_pago = data.get('metodo_pago', 'EFECTIVO')
    observaciones = data.get('observaciones', '')
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'error': 'Debe agregar al menos un producto'}), 400

    pagado = 0
    try:
        pagado = float(data.get('pagado', 0))
    except (ValueError, TypeError):
        pagado = 0

    total = 0
    processed_items = []
    for item in items:
        try:
            cantidad = float(item.get('cantidad', 1))
            precio_unitario = float(item.get('precio_unitario', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Valores numéricos inválidos'}), 400

        if cantidad <= 0 or precio_unitario < 0:
            return jsonify({'success': False, 'error': 'Cantidad y precio deben ser positivos'}), 400

        subtotal = cantidad * precio_unitario
        total += subtotal
        processed_items.append({
            'producto_id': item.get('producto_id'),
            'nombre_producto': item.get('nombre_producto', ''),
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'subtotal': subtotal
        })

    saldo = total - pagado

    db = get_db()
    db.execute(
        'UPDATE compras SET proveedor_id = ?, total = ?, pagado = ?, saldo = ?, metodo_pago = ?, observaciones = ? WHERE id = ?',
        (proveedor_id, total, pagado, saldo, metodo_pago, observaciones, id)
    )
    db.execute('DELETE FROM compra_detalles WHERE compra_id = ?', (id,))

    for item in processed_items:
        db.execute(
            'INSERT INTO compra_detalles (compra_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)',
            (id, item['producto_id'], item['nombre_producto'], item['cantidad'], item['precio_unitario'], item['subtotal'])
        )
        if item['producto_id']:
            db.execute(
                'UPDATE productos SET precio_compra = ? WHERE id = ?',
                (item['precio_unitario'], item['producto_id'])
            )

    db.commit()
    db.close()
    flash('Compra actualizada exitosamente', 'success')
    return jsonify({'success': True, 'compra_id': id})


@transactions.route('/ventas')
@login_required
def ventas_list():
    db = get_db()
    ventas = db.execute('''
        SELECT v.*, c.nombre as cliente_nombre, ve.nombre as vendedor_nombre
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN vendedores ve ON v.vendedor_id = ve.id
        ORDER BY v.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('transactions/ventas.html', ventas=ventas)


@transactions.route('/ventas/nueva', methods=['GET'])
@login_required
def venta_nueva():
    db = get_db()
    clientes = db.execute("SELECT * FROM clientes WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    vendedores = db.execute("SELECT * FROM vendedores WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    productos = db.execute("SELECT * FROM productos WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    db.close()
    return render_template('transactions/venta_form.html', venta=None, clientes=clientes, vendedores=vendedores, productos=productos)


@transactions.route('/ventas/nueva', methods=['POST'])
@login_required
def venta_crear():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    cliente_id = data.get('cliente_id')
    vendedor_id = data.get('vendedor_id')
    metodo_pago = data.get('metodo_pago', 'EFECTIVO')
    observaciones = data.get('observaciones', '')
    items = data.get('items', [])
    fecha = datetime.now().strftime('%Y-%m-%d')

    if not items:
        return jsonify({'success': False, 'error': 'Debe agregar al menos un producto'}), 400

    pagado = 0
    try:
        pagado = float(data.get('pagado', 0))
        descuento_global = float(data.get('descuento', 0))
    except (ValueError, TypeError):
        pagado = 0
        descuento_global = 0

    db = get_db()

    total = 0
    processed_items = []
    for item in items:
        try:
            cantidad = float(item.get('cantidad', 1))
            precio = float(item.get('precio', 0))
            descuento_item = float(item.get('descuento', 0))
        except (ValueError, TypeError):
            db.close()
            return jsonify({'success': False, 'error': 'Valores numéricos inválidos'}), 400

        if cantidad <= 0 or precio < 0:
            db.close()
            return jsonify({'success': False, 'error': 'Cantidad y precio deben ser positivos'}), 400

        subtotal = (cantidad * precio) - descuento_item
        total += subtotal

        costo = 0
        ganancia = 0
        if item.get('producto_id'):
            producto = db.execute('SELECT precio_compra FROM productos WHERE id = ?', (item['producto_id'],)).fetchone()
            if producto:
                costo = producto['precio_compra'] * cantidad
                ganancia = subtotal - costo

        processed_items.append({
            'producto_id': item.get('producto_id'),
            'nombre_producto': item.get('nombre_producto', ''),
            'cantidad': cantidad,
            'precio': precio,
            'descuento': descuento_item,
            'subtotal': subtotal,
            'costo': costo,
            'ganancia': ganancia
        })

    total -= descuento_global
    saldo = total - pagado

    codigo = generar_codigo(db, 'ventas', 'NIB-VTA')
    cursor = db.execute(
        'INSERT INTO ventas (codigo, cliente_id, vendedor_id, fecha, total, descuento, pagado, saldo, metodo_pago, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (codigo, cliente_id, vendedor_id, fecha, total, descuento_global, pagado, saldo, metodo_pago, observaciones)
    )
    venta_id = cursor.lastrowid

    for item in processed_items:
        db.execute(
            'INSERT INTO venta_detalles (venta_id, producto_id, nombre_producto, cantidad, precio, descuento, subtotal, costo, ganancia) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (venta_id, item['producto_id'], item['nombre_producto'], item['cantidad'], item['precio'], item['descuento'], item['subtotal'], item['costo'], item['ganancia'])
        )

    if saldo > 0 and cliente_id:
        db.execute(
            'INSERT INTO cuentas_por_cobrar (venta_id, cliente_id, total, pagado, saldo) VALUES (?, ?, ?, ?, ?)',
            (venta_id, cliente_id, total, pagado, saldo)
        )

    db.commit()
    db.close()
    flash(f'Venta registrada exitosamente con código {codigo}', 'success')
    return jsonify({'success': True, 'venta_id': venta_id, 'codigo': codigo})


@transactions.route('/ventas/<int:id>')
@login_required
def venta_detalle(id):
    db = get_db()
    venta = db.execute('''
        SELECT v.*, c.nombre as cliente_nombre, ve.nombre as vendedor_nombre
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN vendedores ve ON v.vendedor_id = ve.id
        WHERE v.id = ?
    ''', (id,)).fetchone()
    detalles = db.execute('''
        SELECT vd.*, pr.codigo as producto_codigo
        FROM venta_detalles vd
        LEFT JOIN productos pr ON vd.producto_id = pr.id
        WHERE vd.venta_id = ?
    ''', (id,)).fetchall()
    db.close()
    if not venta:
        flash('Venta no encontrada', 'danger')
        return redirect(url_for('transactions.ventas_list'))
    return render_template('transactions/venta_detalle.html', venta=venta, detalles=detalles)


@transactions.route('/ventas/editar/<int:id>', methods=['GET'])
@login_required
def venta_editar_form(id):
    db = get_db()
    venta = db.execute('SELECT * FROM ventas WHERE id = ?', (id,)).fetchone()
    if not venta:
        flash('Venta no encontrada', 'danger')
        db.close()
        return redirect(url_for('transactions.ventas_list'))
    detalles = db.execute('SELECT * FROM venta_detalles WHERE venta_id = ?', (id,)).fetchall()
    clientes = db.execute("SELECT * FROM clientes WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    vendedores = db.execute("SELECT * FROM vendedores WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    productos = db.execute("SELECT * FROM productos WHERE estado = 'ACTIVO' ORDER BY nombre").fetchall()
    db.close()
    return render_template('transactions/venta_form.html', venta=venta, detalles=detalles, clientes=clientes, vendedores=vendedores, productos=productos)


@transactions.route('/ventas/editar/<int:id>', methods=['POST'])
@login_required
def venta_editar(id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    cliente_id = data.get('cliente_id')
    vendedor_id = data.get('vendedor_id')
    metodo_pago = data.get('metodo_pago', 'EFECTIVO')
    observaciones = data.get('observaciones', '')
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'error': 'Debe agregar al menos un producto'}), 400

    pagado = 0
    try:
        pagado = float(data.get('pagado', 0))
        descuento_global = float(data.get('descuento', 0))
    except (ValueError, TypeError):
        pagado = 0
        descuento_global = 0

    db = get_db()

    total = 0
    processed_items = []
    for item in items:
        try:
            cantidad = float(item.get('cantidad', 1))
            precio = float(item.get('precio', 0))
            descuento_item = float(item.get('descuento', 0))
        except (ValueError, TypeError):
            db.close()
            return jsonify({'success': False, 'error': 'Valores numéricos inválidos'}), 400

        if cantidad <= 0 or precio < 0:
            db.close()
            return jsonify({'success': False, 'error': 'Cantidad y precio deben ser positivos'}), 400

        subtotal = (cantidad * precio) - descuento_item
        total += subtotal

        costo = 0
        ganancia = 0
        if item.get('producto_id'):
            producto = db.execute('SELECT precio_compra FROM productos WHERE id = ?', (item['producto_id'],)).fetchone()
            if producto:
                costo = producto['precio_compra'] * cantidad
                ganancia = subtotal - costo

        processed_items.append({
            'producto_id': item.get('producto_id'),
            'nombre_producto': item.get('nombre_producto', ''),
            'cantidad': cantidad,
            'precio': precio,
            'descuento': descuento_item,
            'subtotal': subtotal,
            'costo': costo,
            'ganancia': ganancia
        })

    total -= descuento_global
    saldo = total - pagado

    db.execute(
        'UPDATE ventas SET cliente_id = ?, vendedor_id = ?, total = ?, descuento = ?, pagado = ?, saldo = ?, metodo_pago = ?, observaciones = ? WHERE id = ?',
        (cliente_id, vendedor_id, total, descuento_global, pagado, saldo, metodo_pago, observaciones, id)
    )
    db.execute('DELETE FROM venta_detalles WHERE venta_id = ?', (id,))

    for item in processed_items:
        db.execute(
            'INSERT INTO venta_detalles (venta_id, producto_id, nombre_producto, cantidad, precio, descuento, subtotal, costo, ganancia) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (id, item['producto_id'], item['nombre_producto'], item['cantidad'], item['precio'], item['descuento'], item['subtotal'], item['costo'], item['ganancia'])
        )

    existing_cuenta = db.execute('SELECT id FROM cuentas_por_cobrar WHERE venta_id = ?', (id,)).fetchone()
    if saldo > 0 and cliente_id:
        if existing_cuenta:
            db.execute(
                'UPDATE cuentas_por_cobrar SET cliente_id = ?, total = ?, pagado = ?, saldo = ?, estado = ? WHERE venta_id = ?',
                (cliente_id, total, pagado, saldo, 'PENDIENTE' if saldo > 0 else 'PAGADA', id)
            )
        else:
            db.execute(
                'INSERT INTO cuentas_por_cobrar (venta_id, cliente_id, total, pagado, saldo) VALUES (?, ?, ?, ?, ?)',
                (id, cliente_id, total, pagado, saldo)
            )
    elif existing_cuenta and saldo <= 0:
        db.execute('DELETE FROM cuentas_por_cobrar WHERE venta_id = ?', (id,))

    db.commit()
    db.close()
    flash('Venta actualizada exitosamente', 'success')
    return jsonify({'success': True, 'venta_id': id})


@transactions.route('/cuentas-cobrar')
@login_required
def cuentas_cobrar_list():
    db = get_db()
    filtro_estado = request.args.get('estado', '')
    query = '''
        SELECT cc.*, c.nombre as cliente_nombre, v.fecha as venta_fecha
        FROM cuentas_por_cobrar cc
        LEFT JOIN clientes c ON cc.cliente_id = c.id
        LEFT JOIN ventas v ON cc.venta_id = v.id
    '''
    params = []
    if filtro_estado:
        query += ' WHERE cc.estado = ?'
        params.append(filtro_estado)
    query += ' ORDER BY cc.created_at DESC'
    cuentas = db.execute(query, params).fetchall()
    db.close()
    return render_template('transactions/cuentas_cobrar.html', cuentas=cuentas, filtro_estado=filtro_estado)


@transactions.route('/cuentas-cobrar/<int:id>')
@login_required
def cuenta_detalle(id):
    db = get_db()
    cuenta = db.execute('''
        SELECT cc.*, c.nombre as cliente_nombre, v.fecha as venta_fecha
        FROM cuentas_por_cobrar cc
        LEFT JOIN clientes c ON cc.cliente_id = c.id
        LEFT JOIN ventas v ON cc.venta_id = v.id
        WHERE cc.id = ?
    ''', (id,)).fetchone()
    abonos = db.execute('''
        SELECT * FROM abonos_cobrar WHERE cuenta_id = ? ORDER BY fecha DESC
    ''', (id,)).fetchall()
    db.close()
    if not cuenta:
        flash('Cuenta no encontrada', 'danger')
        return redirect(url_for('transactions.cuentas_cobrar_list'))
    return render_template('transactions/cuenta_detalle.html', cuenta=cuenta, abonos=abonos)


@transactions.route('/cuentas-cobrar/abonar/<int:cuenta_id>', methods=['POST'])
@login_required
def cuenta_abonar(cuenta_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    try:
        monto = float(data.get('monto', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Monto inválido'}), 400

    if monto <= 0:
        return jsonify({'success': False, 'error': 'El monto debe ser mayor a cero'}), 400

    fecha = data.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    metodo_pago = data.get('metodo_pago', 'EFECTIVO')
    observaciones = data.get('observaciones', '')

    db = get_db()
    cuenta = db.execute('SELECT * FROM cuentas_por_cobrar WHERE id = ?', (cuenta_id,)).fetchone()

    if not cuenta:
        db.close()
        return jsonify({'success': False, 'error': 'Cuenta no encontrada'}), 404

    if cuenta['estado'] == 'PAGADA':
        db.close()
        return jsonify({'success': False, 'error': 'Esta cuenta ya está completamente pagada'}), 400

    nuevo_pagado = cuenta['pagado'] + monto
    nuevo_saldo = cuenta['total'] - nuevo_pagado
    nuevo_estado = 'PAGADA' if nuevo_saldo <= 0 else 'PENDIENTE'

    db.execute(
        'INSERT INTO abonos_cobrar (cuenta_id, monto, fecha, metodo_pago, observaciones) VALUES (?, ?, ?, ?, ?)',
        (cuenta_id, monto, fecha, metodo_pago, observaciones)
    )
    db.execute(
        'UPDATE cuentas_por_cobrar SET pagado = ?, saldo = ?, estado = ? WHERE id = ?',
        (nuevo_pagado, nuevo_saldo, nuevo_estado, cuenta_id)
    )

    if cuenta['venta_id']:
        db.execute(
            'UPDATE ventas SET pagado = ?, saldo = ? WHERE id = ?',
            (nuevo_pagado, nuevo_saldo, cuenta['venta_id'])
        )

    db.commit()
    db.close()
    flash('Abono registrado exitosamente', 'success')
    return jsonify({'success': True, 'nuevo_saldo': nuevo_saldo, 'nuevo_estado': nuevo_estado})
