from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db
from utils.decorators import login_required, admin_required
from utils.helpers import validate_password

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def dashboard():
    db = get_db()
    from datetime import date, datetime

    today = date.today().isoformat()
    first_of_month = date.today().replace(day=1).isoformat()

    ventas_dia_row = db.execute(
        "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha = ?",
        (today,)
    ).fetchone()
    ventas_dia = ventas_dia_row['total']

    ventas_mes_row = db.execute(
        "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha >= ?",
        (first_of_month,)
    ).fetchone()
    ventas_mes = ventas_mes_row['total']

    total_ingresos_row = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM ingresos WHERE fecha >= ?",
        (first_of_month,)
    ).fetchone()
    total_ingresos = total_ingresos_row['total']

    total_gastos_row = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM gastos WHERE fecha >= ?",
        (first_of_month,)
    ).fetchone()
    total_gastos = total_gastos_row['total']

    total_costos_row = db.execute(
        "SELECT COALESCE(SUM(costo * cantidad), 0) as total "
        "FROM venta_detalles vd "
        "JOIN ventas v ON vd.venta_id = v.id "
        "WHERE v.fecha >= ?",
        (first_of_month,)
    ).fetchone()
    total_costos = total_costos_row['total']

    ganancia_bruta = ventas_mes - total_costos
    ganancia_neta = total_ingresos - total_gastos

    total_capital_row = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM capital"
    ).fetchone()
    total_capital = total_capital_row['total']

    cuentas_pendientes_row = db.execute(
        "SELECT COALESCE(SUM(saldo), 0) as total FROM cuentas_por_cobrar WHERE estado = 'PENDIENTE'"
    ).fetchone()
    cuentas_pendientes = cuentas_pendientes_row['total']

    total_productos_row = db.execute(
        "SELECT COUNT(*) as total FROM productos WHERE estado = 'ACTIVO'"
    ).fetchone()
    total_productos = total_productos_row['total']

    total_clientes_row = db.execute(
        "SELECT COUNT(*) as total FROM clientes WHERE estado = 'ACTIVO'"
    ).fetchone()
    total_clientes = total_clientes_row['total']

    ventas_recientes = db.execute(
        "SELECT v.*, c.nombre as cliente_nombre, ve.nombre as vendedor_nombre "
        "FROM ventas v "
        "LEFT JOIN clientes c ON v.cliente_id = c.id "
        "LEFT JOIN vendedores ve ON v.vendedor_id = ve.id "
        "ORDER BY v.created_at DESC LIMIT 5"
    ).fetchall()

    monthly_sales = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1)
        for _ in range(i):
            if d.month == 1:
                d = d.replace(year=d.year - 1, month=12)
            else:
                d = d.replace(month=d.month - 1)
        month_start = d.isoformat()
        if d.month == 12:
            month_end = d.replace(year=d.year + 1, month=1, day=1).isoformat()
        else:
            month_end = d.replace(month=d.month + 1, day=1).isoformat()
        sale_row = db.execute(
            "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha >= ? AND fecha < ?",
            (month_start, month_end)
        ).fetchone()
        monthly_sales.append({
            'month': d.strftime('%b %Y'),
            'total': sale_row['total']
        })

    top_products = db.execute(
        "SELECT vd.nombre_producto, SUM(vd.cantidad) as cantidad_vendida, SUM(vd.subtotal) as total_vendido "
        "FROM venta_detalles vd "
        "JOIN ventas v ON vd.venta_id = v.id "
        "WHERE v.fecha >= ? "
        "GROUP BY vd.producto_id, vd.nombre_producto "
        "ORDER BY cantidad_vendida DESC LIMIT 5",
        (first_of_month,)
    ).fetchall()

    today_date = date.today()
    if today_date.month == 1:
        prev_month_start = today_date.replace(year=today_date.year - 1, month=12, day=1).isoformat()
        prev_month_end = today_date.replace(day=1).isoformat()
    else:
        prev_month_start = today_date.replace(month=today_date.month - 1, day=1).isoformat()
        prev_month_end = today_date.replace(day=1).isoformat()

    ventas_mes_anterior_row = db.execute(
        "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha >= ? AND fecha < ?",
        (prev_month_start, prev_month_end)
    ).fetchone()
    ventas_mes_anterior = ventas_mes_anterior_row['total']

    ingresos_mes_anterior_row = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM ingresos WHERE fecha >= ? AND fecha < ?",
        (prev_month_start, prev_month_end)
    ).fetchone()
    ingresos_mes_anterior = ingresos_mes_anterior_row['total']

    gastos_mes_anterior_row = db.execute(
        "SELECT COALESCE(SUM(valor), 0) as total FROM gastos WHERE fecha >= ? AND fecha < ?",
        (prev_month_start, prev_month_end)
    ).fetchone()
    gastos_mes_anterior = gastos_mes_anterior_row['total']

    same_month_last_year_start = today_date.replace(year=today_date.year - 1, day=1).isoformat()
    if today_date.month == 12:
        same_month_last_year_end = today_date.replace(year=today_date.year - 1, month=12 + 1, day=1).isoformat()
    else:
        same_month_last_year_end = today_date.replace(year=today_date.year - 1, month=today_date.month + 1, day=1).isoformat()

    ventas_anio_anterior_row = db.execute(
        "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE fecha >= ? AND fecha < ?",
        (same_month_last_year_start, same_month_last_year_end)
    ).fetchone()
    ventas_anio_anterior = ventas_anio_anterior_row['total']

    ingresos_por_dia = []
    for dow in range(7):
        day_names_short = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab']
        ing_row = db.execute(
            "SELECT COALESCE(SUM(valor), 0) as total FROM ingresos WHERE strftime('%w', fecha) = ? AND fecha >= ?",
            (str(dow), first_of_month)
        ).fetchone()
        ventas_dia_row2 = db.execute(
            "SELECT COALESCE(SUM(total), 0) as total FROM ventas WHERE strftime('%w', fecha) = ? AND fecha >= ?",
            (str(dow), first_of_month)
        ).fetchone()
        ingresos_por_dia.append({
            'dia': day_names_short[dow],
            'ingresos': ing_row['total'],
            'ventas': ventas_dia_row2['total']
        })

    gastos_por_categoria = db.execute(
        "SELECT COALESCE(categoria, 'Sin categoría') as categoria, SUM(valor) as total "
        "FROM gastos WHERE fecha >= ? GROUP BY categoria ORDER BY total DESC",
        (first_of_month,)
    ).fetchall()

    top_vendedores = db.execute(
        "SELECT ve.nombre, SUM(v.total) as total_ventas, COUNT(v.id) as num_ventas "
        "FROM ventas v JOIN vendedores ve ON v.vendedor_id = ve.id "
        "WHERE v.fecha >= ? GROUP BY ve.id, ve.nombre "
        "ORDER BY total_ventas DESC LIMIT 5",
        (first_of_month,)
    ).fetchall()

    socios_activos = db.execute(
        "SELECT nombre, porcentaje, capital_aportado FROM socios WHERE estado = 'ACTIVO' ORDER BY porcentaje DESC"
    ).fetchall()

    distribucion_pendiente_row = db.execute(
        "SELECT COUNT(*) as total FROM distribuciones WHERE estado = 'PENDIENTE'"
    ).fetchone()
    distribucion_pendiente = distribucion_pendiente_row['total']

    compras_recientes = db.execute(
        "SELECT co.*, p.nombre as proveedor_nombre "
        "FROM compras co LEFT JOIN proveedores p ON co.proveedor_id = p.id "
        "ORDER BY co.created_at DESC LIMIT 5"
    ).fetchall()

    cuentas_pendientes_det = db.execute(
        "SELECT cpc.*, cl.nombre as cliente_nombre "
        "FROM cuentas_por_cobrar cpc LEFT JOIN clientes cl ON cpc.cliente_id = cl.id "
        "WHERE cpc.estado = 'PENDIENTE' ORDER BY cpc.created_at DESC LIMIT 5"
    ).fetchall()

    cuentas_pendientes_count_row = db.execute(
        "SELECT COUNT(*) as total FROM cuentas_por_cobrar WHERE estado = 'PENDIENTE'"
    ).fetchone()
    cuentas_pendientes_count = cuentas_pendientes_count_row['total']

    inversiones_activas_row = db.execute(
        "SELECT COALESCE(SUM(monto), 0) as total FROM inversiones WHERE estado = 'ACTIVA'"
    ).fetchone()
    inversiones_activas_total = inversiones_activas_row['total']

    actividad_reciente = []

    recientes_ventas = db.execute(
        "SELECT 'venta' as tipo, v.codigo as codigo, v.total as monto, v.fecha as fecha, "
        "c.nombre as persona, v.created_at as created_at "
        "FROM ventas v LEFT JOIN clientes c ON v.cliente_id = c.id "
        "ORDER BY v.created_at DESC LIMIT 5"
    ).fetchall()
    for r in recientes_ventas:
        actividad_reciente.append(dict(r))

    recientes_compras = db.execute(
        "SELECT 'compra' as tipo, co.codigo as codigo, co.total as monto, co.fecha as fecha, "
        "p.nombre as persona, co.created_at as created_at "
        "FROM compras co LEFT JOIN proveedores p ON co.proveedor_id = p.id "
        "ORDER BY co.created_at DESC LIMIT 5"
    ).fetchall()
    for r in recientes_compras:
        actividad_reciente.append(dict(r))

    recientes_ingresos = db.execute(
        "SELECT 'ingreso' as tipo, concepto as codigo, valor as monto, fecha, "
        "responsable as persona, created_at "
        "FROM ingresos WHERE fecha >= ? ORDER BY created_at DESC LIMIT 5",
        (first_of_month,)
    ).fetchall()
    for r in recientes_ingresos:
        actividad_reciente.append(dict(r))

    recientes_gastos = db.execute(
        "SELECT 'gasto' as tipo, concepto as codigo, valor as monto, fecha, "
        "responsable as persona, created_at "
        "FROM gastos WHERE fecha >= ? ORDER BY created_at DESC LIMIT 5",
        (first_of_month,)
    ).fetchall()
    for r in recientes_gastos:
        actividad_reciente.append(dict(r))

    actividad_reciente.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    actividad_reciente = actividad_reciente[:15]

    db.close()

    return render_template(
        'main/dashboard.html',
        ventas_dia=ventas_dia,
        ventas_mes=ventas_mes,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        total_costos=total_costos,
        ganancia_bruta=ganancia_bruta,
        ganancia_neta=ganancia_neta,
        total_capital=total_capital,
        cuentas_pendientes=cuentas_pendientes,
        total_productos=total_productos,
        total_clientes=total_clientes,
        ventas_recientes=ventas_recientes,
        monthly_sales=monthly_sales,
        top_products=top_products,
        ventas_mes_anterior=ventas_mes_anterior,
        ingresos_mes_anterior=ingresos_mes_anterior,
        gastos_mes_anterior=gastos_mes_anterior,
        ventas_anio_anterior=ventas_anio_anterior,
        ingresos_por_dia=ingresos_por_dia,
        gastos_por_categoria=gastos_por_categoria,
        top_vendedores=top_vendedores,
        socios_activos=socios_activos,
        distribucion_pendiente=distribucion_pendiente,
        compras_recientes=compras_recientes,
        cuentas_pendientes_det=cuentas_pendientes_det,
        cuentas_pendientes_count=cuentas_pendientes_count,
        inversiones_activas_total=inversiones_activas_total,
        actividad_reciente=actividad_reciente
    )


@main.route('/usuarios', methods=['GET', 'POST'])
@login_required
@admin_required
def usuarios():
    db = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        rol = request.form.get('rol', 'VENDEDOR')

        if action == 'create':
            if not username or not password or not nombre:
                flash('Los campos usuario, contraseña y nombre son obligatorios', 'danger')
                return redirect(url_for('main.usuarios'))

            existing = db.execute(
                "SELECT id FROM usuarios WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                flash('El nombre de usuario ya existe', 'danger')
                return redirect(url_for('main.usuarios'))

            pwd_errors = validate_password(password)
            if pwd_errors:
                flash('Contraseña insegura: ' + '; '.join(pwd_errors), 'danger')
                return redirect(url_for('main.usuarios'))

            db.execute(
                "INSERT INTO usuarios (username, password_hash, nombre, email, rol) VALUES (?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), nombre, email, rol)
            )
            db.commit()
            flash('Usuario creado correctamente', 'success')

        elif action == 'edit':
            if not user_id:
                flash('ID de usuario no válido', 'danger')
                return redirect(url_for('main.usuarios'))

            if password:
                pwd_errors = validate_password(password)
                if pwd_errors:
                    flash('Contraseña insegura: ' + '; '.join(pwd_errors), 'danger')
                    return redirect(url_for('main.usuarios'))

                db.execute(
                    "UPDATE usuarios SET username = ?, password_hash = ?, nombre = ?, email = ?, rol = ? WHERE id = ?",
                    (username, generate_password_hash(password), nombre, email, rol, user_id)
                )
            else:
                db.execute(
                    "UPDATE usuarios SET username = ?, nombre = ?, email = ?, rol = ? WHERE id = ?",
                    (username, nombre, email, rol, user_id)
                )
            db.commit()
            flash('Usuario actualizado correctamente', 'success')

        elif action == 'delete':
            if not user_id:
                flash('ID de usuario no válido', 'danger')
                return redirect(url_for('main.usuarios'))

            if str(user_id) == str(session.get('user_id')):
                flash('No puede eliminar su propio usuario', 'danger')
                return redirect(url_for('main.usuarios'))

            try:
                db.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
                db.commit()
                flash('Usuario eliminado correctamente', 'success')
            except Exception:
                flash('Error al eliminar el usuario', 'danger')

        db.close()
        return redirect(url_for('main.usuarios'))

    users = db.execute(
        "SELECT id, username, nombre, email, rol, estado, created_at FROM usuarios ORDER BY created_at DESC"
    ).fetchall()
    db.close()

    return render_template('main/usuarios.html', users=users)
