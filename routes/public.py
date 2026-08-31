import json
from flask import Blueprint, render_template, request, Response, abort
from database.db import get_db

public_bp = Blueprint('public', __name__, url_prefix='/catalogo')


@public_bp.route('/imagen/<int:img_id>', methods=['GET'])
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


@public_bp.route('/', methods=['GET'])
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

    imagenes_por_producto = {}
    if productos:
        ids = [p['id'] for p in productos]
        placeholders = ', '.join(['?'] * len(ids))
        conn = get_db()
        imgs = conn.execute(
            f'''SELECT id, producto_id, es_principal FROM producto_imagenes
                WHERE producto_id IN ({placeholders})
                ORDER BY es_principal DESC, orden, id''',
            ids
        ).fetchall()
        conn.close()
        for img in imgs:
            imagenes_por_producto.setdefault(img['producto_id'], []).append(img['id'])

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
