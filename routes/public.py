import json
from flask import (Blueprint, render_template, request, Response, abort,
                   redirect, url_for, flash, get_flashed_messages)
from database.db import get_db, get_empresa

public_bp = Blueprint('public', __name__)

WHATSAPP_DEFAULT = '573013992470'


# ---------- helpers ----------

def _contar_productos(db):
    return db.execute(
        "SELECT COUNT(*) AS total FROM productos WHERE estado = 'ACTIVO'"
    ).fetchone()['total']


def _categorias_con_conteo(db):
    """Categorias activas con la cantidad de productos activos de cada una."""
    return db.execute(
        """SELECT c.id, c.nombre, c.descripcion, COUNT(p.id) AS total
           FROM categorias c
           LEFT JOIN productos p ON p.categoria_id = c.id AND p.estado = 'ACTIVO'
           WHERE c.estado = 'ACTIVO'
           GROUP BY c.id, c.nombre, c.descripcion
           ORDER BY c.nombre"""
    ).fetchall()


def _conteo_marcas(db):
    return db.execute(
        "SELECT COUNT(DISTINCT marca) AS total FROM productos "
        "WHERE estado = 'ACTIVO' AND marca IS NOT NULL AND marca != ''"
    ).fetchone()['total']


def _imagenes_por_producto(ids):
    """Devuelve {producto_id: [ids de imagenes]} para una lista de productos."""
    if not ids:
        return {}
    placeholders = ', '.join(['?'] * len(ids))
    conn = get_db()
    try:
        imgs = conn.execute(
            f'''SELECT id, producto_id FROM producto_imagenes
                WHERE producto_id IN ({placeholders})
                ORDER BY es_principal DESC, orden, id''',
            ids
        ).fetchall()
    finally:
        conn.close()
    mapa = {}
    for img in imgs:
        mapa.setdefault(img['producto_id'], []).append(img['id'])
    return mapa


def _cobertura_lista(cobertura):
    """Convierte el texto de cobertura (separado por comas o saltos de linea)
    en una lista limpia de ciudades."""
    if not cobertura:
        return []
    partes = cobertura.replace('\n', ',').replace(';', ',').split(',')
    return [p.strip() for p in partes if p.strip()]


# ---------- datos del sitio (inicio y empresa) ----------

def _datos_sitio(destacados=8):
    db = get_db()
    try:
        total_productos = _contar_productos(db)
        categorias = _categorias_con_conteo(db)
        total_marcas = _conteo_marcas(db)
        if destacados:
            destacados_rows = db.execute(
                """SELECT p.id, p.codigo, p.nombre, p.precio_venta, p.marca,
                          c.nombre AS categoria_nombre
                   FROM productos p
                   LEFT JOIN categorias c ON p.categoria_id = c.id
                   WHERE p.estado = 'ACTIVO'
                   ORDER BY p.id DESC
                   LIMIT ?""",
                (destacados,)
            ).fetchall()
        else:
            destacados_rows = []
    finally:
        db.close()

    imgs = _imagenes_por_producto([r['id'] for r in destacados_rows])
    destacados = []
    for r in destacados_rows:
        lista = imgs.get(r['id'], [])
        destacados.append({
            'id': r['id'],
            'nombre': r['nombre'],
            'categoria': r['categoria_nombre'] or '',
            'precio': float(r['precio_venta'] or 0),
            'imagen': lista[0] if lista else None,
        })

    info = get_empresa() or {}
    return {
        'total_productos': total_productos,
        'total_categorias': len([c for c in categorias if c['total']]),
        'total_marcas': total_marcas,
        'categorias': categorias,
        'destacados': destacados,
        'ciudades': _cobertura_lista(info['cobertura'] if 'cobertura' in info.keys() else None),
        'valores': _cobertura_lista(info['valores'] if 'valores' in info.keys() else None),
    }


# ---------- paginas ----------

def render_inicio():
    """Portada publica. Se invoca desde main.dashboard cuando no hay sesion."""
    return render_template('publico/inicio.html', **_datos_sitio())


@public_bp.route('/inicio', methods=['GET'])
def inicio():
    return render_inicio()


@public_bp.route('/empresa', methods=['GET'])
def empresa():
    return render_template('publico/empresa.html', **_datos_sitio(destacados=0))


@public_bp.route('/catalogo/', methods=['GET'])
@public_bp.route('/catalogo', methods=['GET'])
def catalogo():
    db = get_db()

    busqueda = request.args.get('busqueda', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()
    marca = request.args.get('marca', '').strip()

    query = '''
        SELECT p.id, p.codigo, p.nombre, p.descripcion, p.marca, p.precio_venta,
               c.nombre AS categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.estado = 'ACTIVO'
    '''
    params = []

    if busqueda:
        query += ' AND (p.nombre LIKE ? OR p.descripcion LIKE ? OR p.marca LIKE ? OR p.codigo LIKE ?)'
        params.extend([f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])

    if categoria_id:
        query += ' AND p.categoria_id = ?'
        params.append(categoria_id)

    if marca:
        query += ' AND LOWER(p.marca) = LOWER(?)'
        params.append(marca)

    query += ' ORDER BY p.nombre'

    productos = db.execute(query, params).fetchall()
    categorias = db.execute(
        "SELECT id, nombre FROM categorias WHERE estado = 'ACTIVO' ORDER BY nombre"
    ).fetchall()
    marcas = db.execute(
        "SELECT DISTINCT marca FROM productos WHERE estado = 'ACTIVO' "
        "AND marca IS NOT NULL AND marca != '' ORDER BY marca"
    ).fetchall()
    db.close()

    imagenes_por_producto = _imagenes_por_producto([p['id'] for p in productos])

    datos = []
    for p in productos:
        imgs = imagenes_por_producto.get(p['id'], [])
        datos.append({
            'id': p['id'],
            'codigo': p['codigo'],
            'nombre': p['nombre'],
            'descripcion': p['descripcion'] or '',
            'marca': p['marca'] or '',
            'categoria': p['categoria_nombre'] or 'Sin categoría',
            'precio': float(p['precio_venta'] or 0),
            'imagenes': imgs,
        })

    return render_template(
        'publico/catalogo.html',
        productos=productos,
        imagenes_por_producto=imagenes_por_producto,
        datos_json=json.dumps(datos),
        categorias=categorias,
        marcas=marcas,
        busqueda=busqueda,
        categoria_seleccionada=categoria_id,
        marca_seleccionada=marca
    )


@public_bp.route('/catalogo/imagen/<int:img_id>', methods=['GET'])
def producto_imagen(img_id):
    """Sirve una imagen guardada en la base de datos (persistente)."""
    db = get_db()
    row = db.execute(
        'SELECT imagen, mimetype FROM producto_imagenes WHERE id = ?', (img_id,)
    ).fetchone()
    db.close()
    if not row:
        abort(404)
    data = row['imagen']
    if not isinstance(data, bytes):
        data = bytes(data)
    resp = Response(data, mimetype=row['mimetype'] or 'image/jpeg')
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp


# ---------- formulario de contacto ----------

@public_bp.route('/contacto', methods=['POST'])
def contacto():
    nombre = request.form.get('nombre', '').strip()
    email = request.form.get('email', '').strip()
    telefono = request.form.get('telefono', '').strip()
    asunto = request.form.get('asunto', '').strip()
    mensaje = request.form.get('mensaje', '').strip()

    errores = []
    if not nombre:
        errores.append('El nombre es obligatorio.')
    if len(nombre) > 120:
        errores.append('El nombre es demasiado largo.')
    if not mensaje:
        errores.append('El mensaje es obligatorio.')
    if len(mensaje) > 2000:
        errores.append('El mensaje es demasiado largo (maximo 2000 caracteres).')
    if email and ('@' not in email or '.' not in email.split('@')[-1]):
        errores.append('El correo electronico no es valido.')
    if len(email) > 120 or len(telefono) > 40 or len(asunto) > 160:
        errores.append('Alguno de los datos de contacto es demasiado largo.')

    if errores:
        for e in errores:
            flash(e, 'danger')
        return redirect(url_for('public.empresa') + '#contacto')

    # Proteccion basica contra spam: no se aceptan enlaces en exceso
    if mensaje.lower().count('http') > 3:
        flash('No fue posible enviar el mensaje. Intenta escribirnos por WhatsApp.', 'danger')
        return redirect(url_for('public.empresa') + '#contacto')

    db = get_db()
    try:
        db.execute(
            '''INSERT INTO contacto_mensajes (nombre, email, telefono, asunto, mensaje, estado)
               VALUES (?, ?, ?, ?, ?, 'NUEVO')''',
            (nombre, email or None, telefono or None, asunto or None, mensaje)
        )
        db.commit()
    except Exception:
        flash('Ocurrio un error al enviar el mensaje. Intenta de nuevo o escribenos por WhatsApp.', 'danger')
        return redirect(url_for('public.empresa') + '#contacto')
    finally:
        db.close()

    flash('Mensaje enviado. Te responderemos lo antes posible.', 'success')
    return redirect(url_for('public.empresa') + '#contacto')