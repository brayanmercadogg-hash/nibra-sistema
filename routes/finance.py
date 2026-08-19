from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db, generar_codigo
from utils.decorators import login_required, admin_required, partner_or_admin_required

finance = Blueprint('finance', __name__, url_prefix='/finanzas')


@finance.route('/gastos', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def gastos():
    db = get_db()
    if request.method == 'POST':
        concepto = request.form.get('concepto', '').strip()
        categoria = request.form.get('categoria', '').strip()
        fecha = request.form.get('fecha')
        valor = request.form.get('valor', 0, type=float)
        metodo_pago = request.form.get('metodo_pago', 'EFECTIVO')
        responsable = request.form.get('responsable', '').strip()
        observaciones = request.form.get('observaciones', '').strip()

        if not concepto or not fecha:
            flash('Concepto y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.gastos'))

        if valor < 0:
            flash('El valor no puede ser negativo', 'error')
            db.close()
            return redirect(url_for('finance.gastos'))

        try:
            db.execute(
                'INSERT INTO gastos (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones)
            )
            db.commit()
            flash('Gasto registrado correctamente', 'success')
        except Exception:
            flash('Error al registrar el gasto', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.gastos'))

    start = request.args.get('start')
    end = request.args.get('end')

    query = 'SELECT * FROM gastos WHERE 1=1'
    params = []

    if start:
        query += ' AND fecha >= ?'
        params.append(start)
    if end:
        query += ' AND fecha <= ?'
        params.append(end)

    query += ' ORDER BY fecha DESC'
    gastos_list = db.execute(query, params).fetchall()
    total = sum(g['valor'] for g in gastos_list)
    db.close()

    return render_template('finance/gastos.html', gastos=gastos_list, total=total, start=start, end=end)


@finance.route('/gastos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def editar_gasto(id):
    db = get_db()

    if request.method == 'POST':
        concepto = request.form.get('concepto', '').strip()
        categoria = request.form.get('categoria', '').strip()
        fecha = request.form.get('fecha')
        valor = request.form.get('valor', 0, type=float)
        metodo_pago = request.form.get('metodo_pago', 'EFECTIVO')
        responsable = request.form.get('responsable', '').strip()
        observaciones = request.form.get('observaciones', '').strip()

        if not concepto or not fecha:
            flash('Concepto y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.editar_gasto', id=id))

        if valor < 0:
            flash('El valor no puede ser negativo', 'error')
            db.close()
            return redirect(url_for('finance.editar_gasto', id=id))

        try:
            db.execute(
                'UPDATE gastos SET concepto=?, categoria=?, fecha=?, valor=?, metodo_pago=?, responsable=?, observaciones=? WHERE id=?',
                (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones, id)
            )
            db.commit()
            flash('Gasto actualizado correctamente', 'success')
        except Exception:
            flash('Error al actualizar el gasto', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.gastos'))

    gasto = db.execute('SELECT * FROM gastos WHERE id=?', (id,)).fetchone()
    if not gasto:
        flash('Gasto no encontrado', 'error')
        db.close()
        return redirect(url_for('finance.gastos'))

    db.close()
    return render_template('finance/gastos.html', gasto=gasto, editando=True)


@finance.route('/gastos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_gasto(id):
    db = get_db()
    try:
        db.execute('DELETE FROM gastos WHERE id=?', (id,))
        db.commit()
        flash('Gasto eliminado correctamente', 'success')
    except Exception:
        flash('Error al eliminar el gasto', 'error')
    finally:
        db.close()
    return redirect(url_for('finance.gastos'))


@finance.route('/ingresos', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def ingresos():
    db = get_db()
    if request.method == 'POST':
        concepto = request.form.get('concepto', '').strip()
        categoria = request.form.get('categoria', '').strip()
        fecha = request.form.get('fecha')
        valor = request.form.get('valor', 0, type=float)
        metodo_pago = request.form.get('metodo_pago', 'EFECTIVO')
        responsable = request.form.get('responsable', '').strip()
        observaciones = request.form.get('observaciones', '').strip()

        if not concepto or not fecha:
            flash('Concepto y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.ingresos'))

        if valor < 0:
            flash('El valor no puede ser negativo', 'error')
            db.close()
            return redirect(url_for('finance.ingresos'))

        try:
            db.execute(
                'INSERT INTO ingresos (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones)
            )
            db.commit()
            flash('Ingreso registrado correctamente', 'success')
        except Exception:
            flash('Error al registrar el ingreso', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.ingresos'))

    start = request.args.get('start')
    end = request.args.get('end')

    query = 'SELECT * FROM ingresos WHERE 1=1'
    params = []

    if start:
        query += ' AND fecha >= ?'
        params.append(start)
    if end:
        query += ' AND fecha <= ?'
        params.append(end)

    query += ' ORDER BY fecha DESC'
    ingresos_list = db.execute(query, params).fetchall()
    total = sum(i['valor'] for i in ingresos_list)
    db.close()

    return render_template('finance/ingresos.html', ingresos=ingresos_list, total=total, start=start, end=end)


@finance.route('/ingresos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def editar_ingreso(id):
    db = get_db()

    if request.method == 'POST':
        concepto = request.form.get('concepto', '').strip()
        categoria = request.form.get('categoria', '').strip()
        fecha = request.form.get('fecha')
        valor = request.form.get('valor', 0, type=float)
        metodo_pago = request.form.get('metodo_pago', 'EFECTIVO')
        responsable = request.form.get('responsable', '').strip()
        observaciones = request.form.get('observaciones', '').strip()

        if not concepto or not fecha:
            flash('Concepto y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.editar_ingreso', id=id))

        if valor < 0:
            flash('El valor no puede ser negativo', 'error')
            db.close()
            return redirect(url_for('finance.editar_ingreso', id=id))

        try:
            db.execute(
                'UPDATE ingresos SET concepto=?, categoria=?, fecha=?, valor=?, metodo_pago=?, responsable=?, observaciones=? WHERE id=?',
                (concepto, categoria, fecha, valor, metodo_pago, responsable, observaciones, id)
            )
            db.commit()
            flash('Ingreso actualizado correctamente', 'success')
        except Exception:
            flash('Error al actualizar el ingreso', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.ingresos'))

    ingreso = db.execute('SELECT * FROM ingresos WHERE id=?', (id,)).fetchone()
    if not ingreso:
        flash('Ingreso no encontrado', 'error')
        db.close()
        return redirect(url_for('finance.ingresos'))

    db.close()
    return render_template('finance/ingresos.html', ingreso=ingreso, editando=True)


@finance.route('/ingresos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_ingreso(id):
    db = get_db()
    try:
        db.execute('DELETE FROM ingresos WHERE id=?', (id,))
        db.commit()
        flash('Ingreso eliminado correctamente', 'success')
    except Exception:
        flash('Error al eliminar el ingreso', 'error')
    finally:
        db.close()
    return redirect(url_for('finance.ingresos'))


@finance.route('/capital', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def capital():
    db = get_db()
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        concepto = request.form.get('concepto', '').strip()
        valor = request.form.get('valor', 0, type=float)
        fecha = request.form.get('fecha')
        observaciones = request.form.get('observaciones', '').strip()

        if not concepto or not fecha or not tipo:
            flash('Tipo, concepto y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.capital'))

        if valor <= 0:
            flash('El valor debe ser mayor a cero', 'error')
            db.close()
            return redirect(url_for('finance.capital'))

        if tipo not in ('INICIAL', 'APORTE', 'RETIRO'):
            flash('Tipo de movimiento no válido', 'error')
            db.close()
            return redirect(url_for('finance.capital'))

        codigo = generar_codigo(db, 'capital', 'NIB-CAP')
        try:
            db.execute(
                'INSERT INTO capital (codigo, tipo, concepto, valor, fecha, observaciones) VALUES (?, ?, ?, ?, ?, ?)',
                (codigo, tipo, concepto, valor, fecha, observaciones)
            )
            db.commit()
            flash(f'Registro de capital creado correctamente ({codigo})', 'success')
        except Exception:
            flash('Error al crear el registro de capital', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.capital'))

    movimientos = db.execute('SELECT * FROM capital ORDER BY fecha DESC').fetchall()

    inicial = db.execute("SELECT COALESCE(SUM(valor), 0) as total FROM capital WHERE tipo='INICIAL'").fetchone()['total']
    aportes = db.execute("SELECT COALESCE(SUM(valor), 0) as total FROM capital WHERE tipo='APORTE'").fetchone()['total']
    retiros = db.execute("SELECT COALESCE(SUM(valor), 0) as total FROM capital WHERE tipo='RETIRO'").fetchone()['total']
    total_capital = inicial + aportes - retiros
    db.close()

    return render_template('finance/capital.html', movimientos=movimientos, total_capital=total_capital, inicial=inicial, aportes=aportes, retiros=retiros)


@finance.route('/inversiones', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def inversiones():
    db = get_db()
    if request.method == 'POST':
        inversionista = request.form.get('inversionista', '').strip()
        monto = request.form.get('monto', 0, type=float)
        fecha = request.form.get('fecha')
        objetivo = request.form.get('objetivo', '').strip()
        estado = request.form.get('estado', 'ACTIVA')
        retorno = request.form.get('retorno', 0, type=float)
        observaciones = request.form.get('observaciones', '').strip()

        if not inversionista or not fecha:
            flash('Inversionista y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.inversiones'))

        if monto <= 0:
            flash('El monto debe ser mayor a cero', 'error')
            db.close()
            return redirect(url_for('finance.inversiones'))

        codigo = generar_codigo(db, 'inversiones', 'NIB-INV')
        try:
            db.execute(
                'INSERT INTO inversiones (codigo, inversionista, monto, fecha, objetivo, estado, retorno, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (codigo, inversionista, monto, fecha, objetivo, estado, retorno, observaciones)
            )
            db.commit()
            flash(f'Inversión registrada correctamente ({codigo})', 'success')
        except Exception:
            flash('Error al registrar la inversión', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.inversiones'))

    inversiones_list = db.execute('SELECT * FROM inversiones ORDER BY fecha DESC').fetchall()
    db.close()
    return render_template('finance/inversiones.html', inversiones=inversiones_list)


@finance.route('/inversiones/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@partner_or_admin_required
def editar_inversion(id):
    db = get_db()

    if request.method == 'POST':
        inversionista = request.form.get('inversionista', '').strip()
        monto = request.form.get('monto', 0, type=float)
        fecha = request.form.get('fecha')
        objetivo = request.form.get('objetivo', '').strip()
        estado = request.form.get('estado', 'ACTIVA')
        retorno = request.form.get('retorno', 0, type=float)
        observaciones = request.form.get('observaciones', '').strip()

        if not inversionista or not fecha:
            flash('Inversionista y fecha son obligatorios', 'error')
            db.close()
            return redirect(url_for('finance.editar_inversion', id=id))

        if monto <= 0:
            flash('El monto debe ser mayor a cero', 'error')
            db.close()
            return redirect(url_for('finance.editar_inversion', id=id))

        try:
            db.execute(
                'UPDATE inversiones SET inversionista=?, monto=?, fecha=?, objetivo=?, estado=?, retorno=?, observaciones=? WHERE id=?',
                (inversionista, monto, fecha, objetivo, estado, retorno, observaciones, id)
            )
            db.commit()
            flash('Inversión actualizada correctamente', 'success')
        except Exception:
            flash('Error al actualizar la inversión', 'error')
        finally:
            db.close()
        return redirect(url_for('finance.inversiones'))

    inversion = db.execute('SELECT * FROM inversiones WHERE id=?', (id,)).fetchone()
    if not inversion:
        flash('Inversión no encontrada', 'error')
        db.close()
        return redirect(url_for('finance.inversiones'))

    db.close()
    return render_template('finance/inversiones.html', inversion=inversion, editando=True)


@finance.route('/inversiones/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_inversion(id):
    db = get_db()
    try:
        db.execute('DELETE FROM inversiones WHERE id=?', (id,))
        db.commit()
        flash('Inversión eliminada correctamente', 'success')
    except Exception:
        flash('Error al eliminar la inversión', 'error')
    finally:
        db.close()
    return redirect(url_for('finance.inversiones'))


@finance.route('/utilidades')
@login_required
@partner_or_admin_required
def utilidades():
    db = get_db()
    start = request.args.get('start')
    end = request.args.get('end')

    params_ing = []
    query_ing = 'SELECT COALESCE(SUM(valor), 0) as total FROM ingresos WHERE 1=1'
    params_gas = []
    query_gas = 'SELECT COALESCE(SUM(valor), 0) as total FROM gastos WHERE 1=1'
    params_com = []
    query_com = 'SELECT COALESCE(SUM(total), 0) as total FROM compras WHERE 1=1'

    if start:
        query_ing += ' AND fecha >= ?'
        query_gas += ' AND fecha >= ?'
        query_com += ' AND fecha >= ?'
        params_ing.append(start)
        params_gas.append(start)
        params_com.append(start)
    if end:
        query_ing += ' AND fecha <= ?'
        query_gas += ' AND fecha <= ?'
        query_com += ' AND fecha <= ?'
        params_ing.append(end)
        params_gas.append(end)
        params_com.append(end)

    total_ingresos = db.execute(query_ing, params_ing).fetchone()['total']
    total_gastos = db.execute(query_gas, params_gas).fetchone()['total']
    total_costos = db.execute(query_com, params_com).fetchone()['total']

    utilidad_bruta = total_ingresos - total_costos
    utilidad_neta = total_ingresos - total_costos - total_gastos
    distribuible = max(utilidad_neta, 0)

    desglose = []
    gastos_por_concepto = db.execute(
        'SELECT concepto, SUM(valor) as total FROM gastos GROUP BY concepto'
    ).fetchall()
    for g in gastos_por_concepto:
        desglose.append({'concepto': g['concepto'], 'ingresos': 0, 'costos': 0, 'gastos': g['total'], 'utilidad': -g['total']})

    db.close()

    return render_template(
        'finance/utilidades.html',
        total_ingresos=total_ingresos,
        total_costos=total_costos,
        total_gastos=total_gastos,
        utilidad_bruta=utilidad_bruta,
        utilidad_neta=utilidad_neta,
        distribuible=distribuible,
        desglose=desglose,
        start=start,
        end=end
    )
