from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import get_db, generar_codigo
from utils.decorators import login_required, admin_required
import os
from werkzeug.utils import secure_filename

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventario')

@inventory_bp.route('/categorias', methods=['GET'])
@login_required
def categorias():
    db = get_db()
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    db.close()
    return render_template('inventory/categorias.html', categorias=categorias)

@inventory_bp.route('/categorias', methods=['POST'])
@login_required
def crear_categoria():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'error')
        return redirect(url_for('inventory.categorias'))
    db = get_db()
    existing = db.execute('SELECT id FROM categorias WHERE nombre = ?', (nombre,)).fetchone()
    if existing:
        db.close()
        flash('Ya existe una categoría con ese nombre.', 'error')
        return redirect(url_for('inventory.categorias'))
    try:
        db.execute('INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)', (nombre, descripcion))
        db.commit()
        flash('Categoría creada exitosamente.', 'success')
    except Exception:
        flash('Error al crear la categoría.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.categorias'))

@inventory_bp.route('/categorias/editar/<int:id>', methods=['GET'])
@login_required
def editar_categoria(id):
    db = get_db()
    categoria = db.execute('SELECT * FROM categorias WHERE id = ?', (id,)).fetchone()
    if not categoria:
        flash('Categoría no encontrada.', 'error')
        db.close()
        return redirect(url_for('inventory.categorias'))
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    db.close()
    return render_template('inventory/categorias.html', categorias=categorias, categoria=categoria)

@inventory_bp.route('/categorias/editar/<int:id>', methods=['POST'])
@login_required
def actualizar_categoria(id):
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    if not nombre:
        flash('El nombre de la categoría es obligatorio.', 'error')
        return redirect(url_for('inventory.categorias'))
    db = get_db()
    existing = db.execute('SELECT id FROM categorias WHERE nombre = ? AND id != ?', (nombre, id)).fetchone()
    if existing:
        db.close()
        flash('Ya existe otra categoría con ese nombre.', 'error')
        return redirect(url_for('inventory.categorias'))
    try:
        db.execute('UPDATE categorias SET nombre = ?, descripcion = ? WHERE id = ?', (nombre, descripcion, id))
        db.commit()
        flash('Categoría actualizada exitosamente.', 'success')
    except Exception:
        flash('Error al actualizar la categoría.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.categorias'))

@inventory_bp.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_categoria(id):
    db = get_db()
    productos_count = db.execute('SELECT COUNT(*) as cnt FROM productos WHERE categoria_id = ?', (id,)).fetchone()['cnt']
    if productos_count > 0:
        db.close()
        flash(f'No se puede eliminar: existen {productos_count} productos en esta categoría.', 'error')
        return redirect(url_for('inventory.categorias'))
    try:
        db.execute('DELETE FROM categorias WHERE id = ?', (id,))
        db.commit()
        flash('Categoría eliminada exitosamente.', 'success')
    except Exception:
        flash('Error al eliminar la categoría.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.categorias'))

@inventory_bp.route('/productos', methods=['GET'])
@login_required
def productos():
    db = get_db()
    productos = db.execute('''
        SELECT p.*, c.nombre as categoria_nombre 
        FROM productos p 
        LEFT JOIN categorias c ON p.categoria_id = c.id 
        ORDER BY p.nombre
    ''').fetchall()
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    db.close()
    return render_template('inventory/productos.html', productos=productos, categorias=categorias)

@inventory_bp.route('/productos', methods=['POST'])
@login_required
def crear_producto():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    categoria_id = request.form.get('categoria_id')
    marca = request.form.get('marca', '').strip()
    precio_compra = request.form.get('precio_compra', 0)
    precio_venta = request.form.get('precio_venta', 0)
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre del producto es obligatorio.', 'error')
        return redirect(url_for('inventory.productos'))

    try:
        precio_compra = float(precio_compra)
        precio_venta = float(precio_venta)
    except (ValueError, TypeError):
        precio_compra = 0
        precio_venta = 0

    if precio_venta < 0 or precio_compra < 0:
        flash('Los precios no pueden ser negativos.', 'error')
        return redirect(url_for('inventory.productos'))

    margen = 0
    if precio_compra > 0:
        margen = ((precio_venta - precio_compra) / precio_compra) * 100

    imagen = ''
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file.filename:
            allowed = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed:
                flash('Tipo de archivo no permitido.', 'error')
                return redirect(url_for('inventory.productos'))
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'img', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            imagen = filename

    db = get_db()
    codigo = generar_codigo(db, 'productos', 'NIB-PROD')
    try:
        db.execute('''
            INSERT INTO productos (codigo, nombre, descripcion, categoria_id, marca, precio_compra, precio_venta, margen, imagen, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, nombre, descripcion, categoria_id if categoria_id else None, marca, precio_compra, precio_venta, margen, imagen, estado))
        db.commit()
        flash(f'Producto creado exitosamente con código {codigo}.', 'success')
    except Exception:
        flash('Error al crear el producto.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.productos'))

@inventory_bp.route('/productos/editar/<int:id>', methods=['GET'])
@login_required
def editar_producto(id):
    db = get_db()
    producto = db.execute('''
        SELECT p.*, c.nombre as categoria_nombre 
        FROM productos p 
        LEFT JOIN categorias c ON p.categoria_id = c.id 
        WHERE p.id = ?
    ''', (id,)).fetchone()
    if not producto:
        flash('Producto no encontrado.', 'error')
        db.close()
        return redirect(url_for('inventory.productos'))
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    db.close()
    return render_template('inventory/productos.html', producto=producto, categorias=categorias)

@inventory_bp.route('/productos/editar/<int:id>', methods=['POST'])
@login_required
def actualizar_producto(id):
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    categoria_id = request.form.get('categoria_id')
    marca = request.form.get('marca', '').strip()
    precio_compra = request.form.get('precio_compra', 0)
    precio_venta = request.form.get('precio_venta', 0)
    estado = request.form.get('estado', 'ACTIVO')

    if not nombre:
        flash('El nombre del producto es obligatorio.', 'error')
        return redirect(url_for('inventory.productos'))

    try:
        precio_compra = float(precio_compra)
        precio_venta = float(precio_venta)
    except (ValueError, TypeError):
        precio_compra = 0
        precio_venta = 0

    if precio_venta < 0 or precio_compra < 0:
        flash('Los precios no pueden ser negativos.', 'error')
        return redirect(url_for('inventory.productos'))

    margen = 0
    if precio_compra > 0:
        margen = ((precio_venta - precio_compra) / precio_compra) * 100

    imagen = request.form.get('imagen_actual', '')
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file.filename:
            allowed = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed:
                flash('Tipo de archivo no permitido.', 'error')
                return redirect(url_for('inventory.productos'))
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'img', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            imagen = filename

    db = get_db()
    try:
        db.execute('''
            UPDATE productos 
            SET nombre=?, descripcion=?, categoria_id=?, marca=?, precio_compra=?, precio_venta=?, margen=?, imagen=?, estado=?
            WHERE id=?
        ''', (nombre, descripcion, categoria_id if categoria_id else None, marca, precio_compra, precio_venta, margen, imagen, estado, id))
        db.commit()
        flash('Producto actualizado exitosamente.', 'success')
    except Exception:
        flash('Error al actualizar el producto.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.productos'))

@inventory_bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_producto(id):
    db = get_db()
    try:
        db.execute('DELETE FROM productos WHERE id = ?', (id,))
        db.commit()
        flash('Producto eliminado exitosamente.', 'success')
    except Exception:
        flash('Error al eliminar el producto.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.productos'))
