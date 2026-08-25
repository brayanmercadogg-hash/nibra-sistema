from flask import Blueprint, render_template, request, jsonify
from database.db import get_db
from utils.decorators import login_required, partner_or_admin_required
from utils.helpers import export_csv

reports_bp = Blueprint('reports', __name__, url_prefix='/reportes')


@reports_bp.route('/')
@login_required
@partner_or_admin_required
def index():
    return render_template('reports/reportes.html')


@reports_bp.route('/generar')
@login_required
@partner_or_admin_required
def generar():
    tipo = request.args.get('tipo', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    db = get_db()

    report_configs = {
        'ventas': {
            'query': '''
                SELECT v.id, v.fecha, c.nombre as cliente, vendedor.nombre as vendedor,
                       v.total, v.descuento, v.pagado, v.saldo, v.metodo_pago
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN vendedores vendedor ON v.vendedor_id = vendedor.id
                WHERE v.fecha BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            ''',
            'columns': ['id', 'fecha', 'cliente', 'vendedor', 'total', 'descuento', 'pagado', 'saldo', 'metodo_pago'],
            'titulo': 'Reporte de Ventas'
        },
        'compras': {
            'query': '''
                SELECT cp.id, cp.fecha, pr.nombre as proveedor, cp.total,
                       cp.pagado, cp.saldo, cp.metodo_pago
                FROM compras cp
                LEFT JOIN proveedores pr ON cp.proveedor_id = pr.id
                WHERE cp.fecha BETWEEN ? AND ?
                ORDER BY cp.fecha DESC
            ''',
            'columns': ['id', 'fecha', 'proveedor', 'total', 'pagado', 'saldo', 'metodo_pago'],
            'titulo': 'Reporte de Compras'
        },
        'ingresos': {
            'query': '''
                SELECT id, fecha, concepto, categoria, valor, metodo_pago, responsable
                FROM ingresos
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'concepto', 'categoria', 'valor', 'metodo_pago', 'responsable'],
            'titulo': 'Reporte de Ingresos'
        },
        'gastos': {
            'query': '''
                SELECT id, fecha, concepto, categoria, valor, metodo_pago, responsable
                FROM gastos
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'concepto', 'categoria', 'valor', 'metodo_pago', 'responsable'],
            'titulo': 'Reporte de Gastos'
        },
        'ganancias': {
            'query': '''
                SELECT v.fecha, v.id as venta_id, vd.nombre_producto, vd.cantidad,
                       vd.precio, vd.subtotal, vd.costo, vd.ganancia
                FROM venta_detalles vd
                JOIN ventas v ON vd.venta_id = v.id
                WHERE v.fecha BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            ''',
            'columns': ['fecha', 'venta_id', 'nombre_producto', 'cantidad', 'precio', 'subtotal', 'costo', 'ganancia'],
            'titulo': 'Reporte de Ganancias'
        },
        'cuentas_cobrar': {
            'query': '''
                SELECT cc.id, cc.created_at as fecha, c.nombre as cliente,
                       cc.total, cc.pagado, cc.saldo, cc.estado
                FROM cuentas_por_cobrar cc
                LEFT JOIN clientes c ON cc.cliente_id = c.id
                WHERE cc.created_at BETWEEN ? AND ?
                ORDER BY cc.created_at DESC
            ''',
            'columns': ['id', 'fecha', 'cliente', 'total', 'pagado', 'saldo', 'estado'],
            'titulo': 'Reporte de Cuentas por Cobrar'
        },
        'capital': {
            'query': '''
                SELECT id, fecha, tipo, concepto, valor
                FROM capital
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'tipo', 'concepto', 'valor'],
            'titulo': 'Reporte de Capital'
        },
        'socios': {
            'query': '''
                SELECT s.id, s.nombre, s.porcentaje, s.capital_aportado,
                       s.fecha_ingreso, s.estado
                FROM socios s
                WHERE s.fecha_ingreso BETWEEN ? AND ?
                ORDER BY s.nombre
            ''',
            'columns': ['id', 'nombre', 'porcentaje', 'capital_aportado', 'fecha_ingreso', 'estado'],
            'titulo': 'Reporte de Socios'
        },
        'inversiones': {
            'query': '''
                SELECT id, fecha, inversionista, monto, objetivo, estado, retorno
                FROM inversiones
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'inversionista', 'monto', 'objetivo', 'estado', 'retorno'],
            'titulo': 'Reporte de Inversiones'
        },
        'comisiones': {
            'query': '''
                SELECT cm.id, cm.created_at as fecha, v.nombre as vendedor,
                       cm.porcentaje, cm.monto, cm.pagado, cm.pendiente
                FROM comisiones cm
                LEFT JOIN vendedores v ON cm.vendedor_id = v.id
                WHERE cm.created_at BETWEEN ? AND ?
                ORDER BY cm.created_at DESC
            ''',
            'columns': ['id', 'fecha', 'vendedor', 'porcentaje', 'monto', 'pagado', 'pendiente'],
            'titulo': 'Reporte de Comisiones'
        }
    }

    if tipo not in report_configs:
        return jsonify({'error': 'Tipo de reporte no válido'}), 400

    config = report_configs[tipo]
    datos = db.execute(config['query'], (fecha_inicio, fecha_fin)).fetchall()
    db.close()
    datos_list = [dict(row) for row in datos]

    total = sum(row.get('total', row.get('valor', row.get('monto', 0)) or 0) for row in datos_list)

    return render_template(
        'reports/reporte_detalle.html',
        tipo=tipo,
        titulo=config['titulo'],
        datos=datos_list,
        columns=config['columns'],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        total=total
    )


@reports_bp.route('/exportar')
@login_required
@partner_or_admin_required
def exportar():
    tipo = request.args.get('tipo', '')
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    db = get_db()

    report_configs = {
        'ventas': {
            'query': '''
                SELECT v.id, v.fecha, c.nombre as cliente, vendedor.nombre as vendedor,
                       v.total, v.descuento, v.pagado, v.saldo, v.metodo_pago
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN vendedores vendedor ON v.vendedor_id = vendedor.id
                WHERE v.fecha BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            ''',
            'columns': ['id', 'fecha', 'cliente', 'vendedor', 'total', 'descuento', 'pagado', 'saldo', 'metodo_pago'],
            'filename': 'ventas.csv'
        },
        'compras': {
            'query': '''
                SELECT cp.id, cp.fecha, pr.nombre as proveedor, cp.total,
                       cp.pagado, cp.saldo, cp.metodo_pago
                FROM compras cp
                LEFT JOIN proveedores pr ON cp.proveedor_id = pr.id
                WHERE cp.fecha BETWEEN ? AND ?
                ORDER BY cp.fecha DESC
            ''',
            'columns': ['id', 'fecha', 'proveedor', 'total', 'pagado', 'saldo', 'metodo_pago'],
            'filename': 'compras.csv'
        },
        'ingresos': {
            'query': '''
                SELECT id, fecha, concepto, categoria, valor, metodo_pago, responsable
                FROM ingresos
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'concepto', 'categoria', 'valor', 'metodo_pago', 'responsable'],
            'filename': 'ingresos.csv'
        },
        'gastos': {
            'query': '''
                SELECT id, fecha, concepto, categoria, valor, metodo_pago, responsable
                FROM gastos
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'concepto', 'categoria', 'valor', 'metodo_pago', 'responsable'],
            'filename': 'gastos.csv'
        },
        'ganancias': {
            'query': '''
                SELECT v.fecha, v.id as venta_id, vd.nombre_producto, vd.cantidad,
                       vd.precio, vd.subtotal, vd.costo, vd.ganancia
                FROM venta_detalles vd
                JOIN ventas v ON vd.venta_id = v.id
                WHERE v.fecha BETWEEN ? AND ?
                ORDER BY v.fecha DESC
            ''',
            'columns': ['fecha', 'venta_id', 'nombre_producto', 'cantidad', 'precio', 'subtotal', 'costo', 'ganancia'],
            'filename': 'ganancias.csv'
        },
        'cuentas_cobrar': {
            'query': '''
                SELECT cc.id, cc.created_at as fecha, c.nombre as cliente,
                       cc.total, cc.pagado, cc.saldo, cc.estado
                FROM cuentas_por_cobrar cc
                LEFT JOIN clientes c ON cc.cliente_id = c.id
                WHERE cc.created_at BETWEEN ? AND ?
                ORDER BY cc.created_at DESC
            ''',
            'columns': ['id', 'fecha', 'cliente', 'total', 'pagado', 'saldo', 'estado'],
            'filename': 'cuentas_por_cobrar.csv'
        },
        'capital': {
            'query': '''
                SELECT id, fecha, tipo, concepto, valor
                FROM capital
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'tipo', 'concepto', 'valor'],
            'filename': 'capital.csv'
        },
        'socios': {
            'query': '''
                SELECT s.id, s.nombre, s.porcentaje, s.capital_aportado,
                       s.fecha_ingreso, s.estado
                FROM socios s
                WHERE s.fecha_ingreso BETWEEN ? AND ?
                ORDER BY s.nombre
            ''',
            'columns': ['id', 'nombre', 'porcentaje', 'capital_aportado', 'fecha_ingreso', 'estado'],
            'filename': 'socios.csv'
        },
        'inversiones': {
            'query': '''
                SELECT id, fecha, inversionista, monto, objetivo, estado, retorno
                FROM inversiones
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            ''',
            'columns': ['id', 'fecha', 'inversionista', 'monto', 'objetivo', 'estado', 'retorno'],
            'filename': 'inversiones.csv'
        },
        'comisiones': {
            'query': '''
                SELECT cm.id, cm.created_at as fecha, v.nombre as vendedor,
                       cm.porcentaje, cm.monto, cm.pagado, cm.pendiente
                FROM comisiones cm
                LEFT JOIN vendedores v ON cm.vendedor_id = v.id
                WHERE cm.created_at BETWEEN ? AND ?
                ORDER BY cm.created_at DESC
            ''',
            'columns': ['id', 'fecha', 'vendedor', 'porcentaje', 'monto', 'pagado', 'pendiente'],
            'filename': 'comisiones.csv'
        }
    }

    if tipo not in report_configs:
        return jsonify({'error': 'Tipo de reporte no válido'}), 400

    config = report_configs[tipo]
    datos = db.execute(config['query'], (fecha_inicio, fecha_fin)).fetchall()
    db.close()
    datos_list = [dict(row) for row in datos]

    return export_csv(datos_list, config['columns'], config['filename'])
