from flask import Blueprint, render_template, request
from database.db import get_db

public_bp = Blueprint('public', __name__, url_prefix='/catalogo')


@public_bp.route('/', methods=['GET'])
def catalogo():
    db = get_db()

    busqueda = request.args.get('busqueda', '').strip()
    categoria_id = request.args.get('categoria_id', '').strip()

    query = '''
        SELECT p.imagen, p.nombre, p.descripcion, p.precio_venta,
               c.nombre AS categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.estado = 'ACTIVO'
    '''
    params = []

    if busqueda:
        query += ' AND (p.nombre LIKE ? OR p.descripcion LIKE ?)'
        params.extend([f'%{busqueda}%', f'%{busqueda}%'])

    if categoria_id:
        query += ' AND p.categoria_id = ?'
        params.append(categoria_id)

    query += ' ORDER BY p.nombre'

    productos = db.execute(query, params).fetchall()
    categorias = db.execute(
        "SELECT id, nombre FROM categorias WHERE estado = 'ACTIVO' ORDER BY nombre"
    ).fetchall()

    return render_template(
        'public/catalogo.html',
        productos=productos,
        categorias=categorias,
        busqueda=busqueda,
        categoria_seleccionada=categoria_id
    )
