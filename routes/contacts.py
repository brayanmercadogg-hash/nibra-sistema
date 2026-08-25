from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db, generar_codigo
from utils.decorators import login_required, admin_required

contacts = Blueprint('contacts', __name__, url_prefix='/contactos')


@contacts.route('/clientes')
@login_required
def clientes():
    db = get_db()
    search = request.args.get('search', '').strip()
    if search:
        clientes = db.execute(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR email LIKE ? OR telefono LIKE ? OR documento LIKE ? OR codigo LIKE ? ORDER BY nombre",
            (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        clientes = db.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    db.close()
    return render_template('contacts/clientes.html', clientes=clientes, search=search)


@contacts.route('/clientes/crear', methods=['POST'])
@login_required
def cliente_crear():
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    direccion = request.form.get('direccion', '').strip()
    documento = request.form.get('documento', '').strip()
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('contacts.clientes'))

    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('El correo electrónico no es válido', 'error')
            return redirect(url_for('contacts.clientes'))

    db = get_db()
    codigo = generar_codigo(db, 'clientes', 'NIB-CLI')
    try:
        db.execute(
            "INSERT INTO clientes (codigo, nombre, email, telefono, direccion, documento, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (codigo, nombre, email, telefono, direccion, documento, estado)
        )
        db.commit()
        flash(f'Cliente creado correctamente con código {codigo}', 'success')
    except Exception:
        flash('Error al crear el cliente', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.clientes'))


@contacts.route('/clientes/editar/<int:id>')
@login_required
def cliente_editar(id):
    db = get_db()
    cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    if not cliente:
        flash('Cliente no encontrado', 'error')
        db.close()
        return redirect(url_for('contacts.clientes'))
    clientes = db.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    db.close()
    return render_template('contacts/clientes.html', clientes=clientes, cliente=cliente, editing=True)


@contacts.route('/clientes/editar/<int:id>', methods=['POST'])
@login_required
def cliente_update(id):
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    direccion = request.form.get('direccion', '').strip()
    documento = request.form.get('documento', '').strip()
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('contacts.clientes'))

    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('El correo electrónico no es válido', 'error')
            return redirect(url_for('contacts.clientes'))

    db = get_db()
    try:
        db.execute(
            "UPDATE clientes SET nombre=?, email=?, telefono=?, direccion=?, documento=?, estado=? WHERE id=?",
            (nombre, email, telefono, direccion, documento, estado, id)
        )
        db.commit()
        flash('Cliente actualizado correctamente', 'success')
    except Exception:
        flash('Error al actualizar el cliente', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.clientes'))


@contacts.route('/clientes/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def cliente_eliminar(id):
    db = get_db()
    try:
        # Se desvinculan las ventas/cuentas (el historial se conserva)
        db.execute("UPDATE ventas SET cliente_id = NULL WHERE cliente_id = ?", (id,))
        db.execute("UPDATE cuentas_por_cobrar SET cliente_id = NULL WHERE cliente_id = ?", (id,))
        db.execute("DELETE FROM clientes WHERE id = ?", (id,))
        db.commit()
        flash('Cliente eliminado correctamente', 'success')
    except Exception as e:
        print(f"ERROR eliminar cliente: {e}")
        flash('Error al eliminar el cliente', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.clientes'))


@contacts.route('/clientes/<int:id>')
@login_required
def cliente_detalle(id):
    db = get_db()
    cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    if not cliente:
        flash('Cliente no encontrado', 'error')
        db.close()
        return redirect(url_for('contacts.clientes'))
    ventas = db.execute(
        "SELECT * FROM ventas WHERE cliente_id = ? ORDER BY fecha DESC",
        (id,)
    ).fetchall()
    db.close()
    return render_template('contacts/cliente_detalle.html', cliente=cliente, ventas=ventas)


@contacts.route('/proveedores')
@login_required
def proveedores():
    db = get_db()
    search = request.args.get('search', '').strip()
    if search:
        proveedores = db.execute(
            "SELECT * FROM proveedores WHERE nombre LIKE ? OR email LIKE ? OR telefono LIKE ? OR documento LIKE ? OR codigo LIKE ? ORDER BY nombre",
            (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        proveedores = db.execute("SELECT * FROM proveedores ORDER BY nombre").fetchall()
    db.close()
    return render_template('contacts/proveedores.html', proveedores=proveedores, search=search)


@contacts.route('/proveedores/crear', methods=['POST'])
@login_required
def proveedor_crear():
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    direccion = request.form.get('direccion', '').strip()
    documento = request.form.get('documento', '').strip()
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('contacts.proveedores'))

    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('El correo electrónico no es válido', 'error')
            return redirect(url_for('contacts.proveedores'))

    db = get_db()
    codigo = generar_codigo(db, 'proveedores', 'NIB-PROV')
    try:
        db.execute(
            "INSERT INTO proveedores (codigo, nombre, email, telefono, direccion, documento, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (codigo, nombre, email, telefono, direccion, documento, estado)
        )
        db.commit()
        flash(f'Proveedor creado correctamente con código {codigo}', 'success')
    except Exception:
        flash('Error al crear el proveedor', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.proveedores'))


@contacts.route('/proveedores/editar/<int:id>')
@login_required
def proveedor_editar(id):
    db = get_db()
    proveedor = db.execute("SELECT * FROM proveedores WHERE id = ?", (id,)).fetchone()
    if not proveedor:
        flash('Proveedor no encontrado', 'error')
        db.close()
        return redirect(url_for('contacts.proveedores'))
    proveedores = db.execute("SELECT * FROM proveedores ORDER BY nombre").fetchall()
    db.close()
    return render_template('contacts/proveedores.html', proveedores=proveedores, proveedor=proveedor, editing=True)


@contacts.route('/proveedores/editar/<int:id>', methods=['POST'])
@login_required
def proveedor_update(id):
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    direccion = request.form.get('direccion', '').strip()
    documento = request.form.get('documento', '').strip()
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre es obligatorio', 'error')
        return redirect(url_for('contacts.proveedores'))

    if email:
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('El correo electrónico no es válido', 'error')
            return redirect(url_for('contacts.proveedores'))

    db = get_db()
    try:
        db.execute(
            "UPDATE proveedores SET nombre=?, email=?, telefono=?, direccion=?, documento=?, estado=? WHERE id=?",
            (nombre, email, telefono, direccion, documento, estado, id)
        )
        db.commit()
        flash('Proveedor actualizado correctamente', 'success')
    except Exception:
        flash('Error al actualizar el proveedor', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.proveedores'))


@contacts.route('/proveedores/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def proveedor_eliminar(id):
    db = get_db()
    try:
        # Se desvinculan las compras (el historial se conserva)
        db.execute("UPDATE compras SET proveedor_id = NULL WHERE proveedor_id = ?", (id,))
        db.execute("DELETE FROM proveedores WHERE id = ?", (id,))
        db.commit()
        flash('Proveedor eliminado correctamente', 'success')
    except Exception as e:
        print(f"ERROR eliminar proveedor: {e}")
        flash('Error al eliminar el proveedor', 'error')
    finally:
        db.close()
    return redirect(url_for('contacts.proveedores'))


@contacts.route('/proveedores/<int:id>')
@login_required
def proveedor_detalle(id):
    db = get_db()
    proveedor = db.execute("SELECT * FROM proveedores WHERE id = ?", (id,)).fetchone()
    if not proveedor:
        flash('Proveedor no encontrado', 'error')
        db.close()
        return redirect(url_for('contacts.proveedores'))
    compras = db.execute(
        "SELECT * FROM compras WHERE proveedor_id = ? ORDER BY fecha DESC",
        (id,)
    ).fetchall()
    db.close()
    return render_template('contacts/proveedor_detalle.html', proveedor=proveedor, compras=compras)
