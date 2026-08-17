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
        top_products=top_products
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
