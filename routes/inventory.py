from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from database.db import get_db, generar_codigo, _is_postgres
from utils.decorators import login_required, admin_required
import os

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventario')

EXTENSIONES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MIMETYPES = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
             '.gif': 'image/gif', '.webp': 'image/webp'}
MAX_IMAGEN_BYTES = 8 * 1024 * 1024


def _guardar_imagen(db, producto_id, file, es_principal=0, orden=0):
    """Guarda una imagen en la DB (persistente). Retorna (ok, mensaje)."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        return False, f'Tipo de archivo no permitido: {file.filename}'
    data = file.read()
    if len(data) == 0:
        return False, f'Archivo vacío: {file.filename}'
    if len(data) > MAX_IMAGEN_BYTES:
        return False, f'La imagen {file.filename} supera el máximo de 8MB.'
    payload = memoryview(data) if _is_postgres() else data
    db.execute(
        '''INSERT INTO producto_imagenes (producto_id, imagen, mimetype, es_principal, orden)
           VALUES (?, ?, ?, ?, ?)''',
        (producto_id, payload, MIMETYPES.get(ext, 'image/jpeg'), es_principal, orden)
    )
    return True, ''

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
        SELECT p.*, c.nombre as categoria_nombre,
               (SELECT pi.id FROM producto_imagenes pi
                WHERE pi.producto_id = p.id
                ORDER BY pi.es_principal DESC, pi.orden, pi.id LIMIT 1) AS imagen_id,
               (SELECT COUNT(*) FROM producto_imagenes pi2 WHERE pi2.producto_id = p.id) AS total_imagenes
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

    archivos = [f for f in request.files.getlist('imagenes') if f and f.filename]
    for file in archivos:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in EXTENSIONES_PERMITIDAS:
            flash(f'Tipo de archivo no permitido: {file.filename}', 'error')
            return redirect(url_for('inventory.productos'))

    db = get_db()
    codigo = generar_codigo(db, 'productos', 'NIB-PROD')
    try:
        cur = db.execute('''
            INSERT INTO productos (codigo, nombre, descripcion, categoria_id, marca, precio_compra, precio_venta, margen, imagen, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ''', (codigo, nombre, descripcion, categoria_id if categoria_id else None, marca, precio_compra, precio_venta, margen, estado))
        producto_id = cur.lastrowid

        errores_img = []
        principal_set = False
        for i, file in enumerate(archivos):
            ok, msg = _guardar_imagen(db, producto_id, file, es_principal=1 if not principal_set else 0, orden=i)
            if ok and not principal_set:
                principal_set = True
            elif not ok:
                errores_img.append(msg)
        db.commit()
        flash(f'Producto creado exitosamente con código {codigo}.', 'success')
        for msg in errores_img:
            flash(msg, 'error')
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
    imagenes = db.execute(
        'SELECT id, es_principal FROM producto_imagenes WHERE producto_id = ? ORDER BY es_principal DESC, orden, id',
        (id,)
    ).fetchall()
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    db.close()
    return render_template('inventory/productos.html', producto=producto, imagenes=imagenes, categorias=categorias)

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
        return redirect(url_for('inventory.editar_producto', id=id))

    margen = 0
    if precio_compra > 0:
        margen = ((precio_venta - precio_compra) / precio_compra) * 100

    archivos = [f for f in request.files.getlist('imagenes') if f and f.filename]
    for file in archivos:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in EXTENSIONES_PERMITIDAS:
            flash(f'Tipo de archivo no permitido: {file.filename}', 'error')
            return redirect(url_for('inventory.editar_producto', id=id))

    db = get_db()
    try:
        db.execute('''
            UPDATE productos
            SET nombre=?, descripcion=?, categoria_id=?, marca=?, precio_compra=?, precio_venta=?, margen=?, imagen=NULL, estado=?
            WHERE id=?
        ''', (nombre, descripcion, categoria_id if categoria_id else None, marca, precio_compra, precio_venta, margen, estado, id))

        tiene_imagenes = db.execute(
            'SELECT COUNT(*) AS cnt FROM producto_imagenes WHERE producto_id = ?', (id,)
        ).fetchone()['cnt']

        errores_img = []
        orden_base = int(tiene_imagenes)
        marcar_primera = int(tiene_imagenes) == 0
        for i, file in enumerate(archivos):
            ok, msg = _guardar_imagen(db, id, file, es_principal=1 if marcar_primera else 0, orden=orden_base + i)
            if ok:
                marcar_primera = False
            elif not ok:
                errores_img.append(msg)
        db.commit()
        flash('Producto actualizado exitosamente.', 'success')
        for msg in errores_img:
            flash(msg, 'error')
    except Exception:
        flash('Error al actualizar el producto.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.editar_producto', id=id))

@inventory_bp.route('/productos/imagenes/<int:img_id>/eliminar', methods=['POST'])
@login_required
def eliminar_imagen(img_id):
    db = get_db()
    img = db.execute('SELECT id, producto_id, es_principal FROM producto_imagenes WHERE id = ?', (img_id,)).fetchone()
    if not img:
        db.close()
        flash('Imagen no encontrada.', 'error')
        return redirect(url_for('inventory.productos'))
    producto_id = img['producto_id']
    try:
        db.execute('DELETE FROM producto_imagenes WHERE id = ?', (img_id,))
        restantes = db.execute(
            'SELECT id FROM producto_imagenes WHERE producto_id = ? ORDER BY orden, id LIMIT 1',
            (producto_id,)
        ).fetchone()
        if restantes and img['es_principal']:
            db.execute('UPDATE producto_imagenes SET es_principal = 1 WHERE id = ?', (restantes['id'],))
        db.commit()
        flash('Imagen eliminada exitosamente.', 'success')
    except Exception:
        flash('Error al eliminar la imagen.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.editar_producto', id=producto_id))

@inventory_bp.route('/productos/imagenes/<int:img_id>/principal', methods=['POST'])
@login_required
def imagen_principal(img_id):
    db = get_db()
    img = db.execute('SELECT producto_id FROM producto_imagenes WHERE id = ?', (img_id,)).fetchone()
    if not img:
        db.close()
        flash('Imagen no encontrada.', 'error')
        return redirect(url_for('inventory.productos'))
    producto_id = img['producto_id']
    try:
        db.execute('UPDATE producto_imagenes SET es_principal = 0 WHERE producto_id = ?', (producto_id,))
        db.execute('UPDATE producto_imagenes SET es_principal = 1 WHERE id = ?', (img_id,))
        db.commit()
        flash('Imagen principal actualizada.', 'success')
    except Exception:
        flash('Error al actualizar la imagen principal.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.editar_producto', id=producto_id))

@inventory_bp.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_producto(id):
    db = get_db()
    try:
        db.execute('DELETE FROM producto_imagenes WHERE producto_id = ?', (id,))
        db.execute('DELETE FROM productos WHERE id = ?', (id,))
        db.commit()
        flash('Producto eliminado exitosamente.', 'success')
    except Exception:
        flash('Error al eliminar el producto.', 'error')
    finally:
        db.close()
    return redirect(url_for('inventory.productos'))
