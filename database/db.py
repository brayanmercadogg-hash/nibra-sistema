import re
from config import Config

DATABASE_URL = Config.DATABASE

def _is_postgres():
    return DATABASE_URL.startswith('postgresql')


class _PgCursorWrapper:
    def __init__(self, cursor, inserted_id=None):
        self._cursor = cursor
        self._inserted_id = inserted_id

    def fetchone(self):
        row = self._cursor.fetchone()
        return row

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return self._inserted_id if self._inserted_id is not None else self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount


class _PgConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        sql = sql.replace("strftime('%w', fecha)", "EXTRACT(DOW FROM fecha)::INTEGER")
        sql = sql.replace("strftime('%m', fecha)", "EXTRACT(MONTH FROM fecha)::INTEGER")
        sql = sql.replace("strftime('%Y', fecha)", "EXTRACT(YEAR FROM fecha)::INTEGER")
        sql = re.sub(r'\?(?!\?)', '%s', sql)
        cur = self._conn.cursor()
        inserted_id = None
        sql_stripped = sql.strip().upper()
        if sql_stripped.startswith('INSERT') and 'RETURNING' not in sql_stripped:
            sql = sql.rstrip().rstrip(';') + ' RETURNING id'
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            row = cur.fetchone()
            if row:
                inserted_id = row['id'] if isinstance(row, dict) else row[0]
        else:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
        return _PgCursorWrapper(cur, inserted_id)

    def executescript(self, script):
        cur = self._conn.cursor()
        cur.execute(script)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def cursor(self):
        return self._conn.cursor()

    @property
    def autocommit(self):
        return self._conn.autocommit

    @autocommit.setter
    def autocommit(self, val):
        self._conn.autocommit = val


def get_db():
    if _is_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = False
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return _PgConnWrapper(conn)
    else:
        import sqlite3
        conn = sqlite3.connect(DATABASE_URL.replace('sqlite:///', ''))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def generar_codigo(db, tabla, prefijo, campo='codigo'):
    if _is_postgres():
        sql = f"SELECT {campo} FROM {tabla} WHERE {campo} LIKE %s ORDER BY id DESC LIMIT 1"
        cur = db.cursor()
        cur.execute(sql, (f'{prefijo}-%',))
        last = cur.fetchone()
        if last:
            val = last[campo]
            num = int(val.split('-')[-1]) + 1
        else:
            num = 1
    else:
        last = db.execute(f"SELECT {campo} FROM {tabla} WHERE {campo} LIKE ? ORDER BY id DESC LIMIT 1", (f'{prefijo}-%',)).fetchone()
        if last:
            num = int(last[campo].split('-')[-1]) + 1
        else:
            num = 1
    return f'{prefijo}-{num:05d}'


def init_db():
    conn = get_db()
    if _is_postgres():
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            email TEXT,
            rol TEXT NOT NULL DEFAULT 'VENDEDOR',
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            debe_cambiar_contrasena INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            categoria_id INTEGER REFERENCES categorias(id),
            marca TEXT,
            precio_compra REAL NOT NULL DEFAULT 0,
            precio_venta REAL NOT NULL DEFAULT 0,
            margen REAL DEFAULT 0,
            imagen TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            direccion TEXT,
            documento TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            direccion TEXT,
            documento TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS vendedores (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id),
            nombre TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            porcentaje_comision REAL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS socios (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            porcentaje REAL NOT NULL DEFAULT 0,
            capital_aportado REAL DEFAULT 0,
            fecha_ingreso DATE,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS compras (
            id SERIAL PRIMARY KEY,
            proveedor_id INTEGER REFERENCES proveedores(id),
            fecha DATE NOT NULL,
            total REAL NOT NULL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0,
            saldo REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO',
            observaciones TEXT,
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS compra_detalles (
            id SERIAL PRIMARY KEY,
            compra_id INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1,
            precio_unitario REAL NOT NULL DEFAULT 0,
            subtotal REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            vendedor_id INTEGER REFERENCES vendedores(id),
            fecha DATE NOT NULL,
            total REAL NOT NULL DEFAULT 0,
            descuento REAL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0,
            saldo REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO',
            observaciones TEXT,
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS venta_detalles (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos(id),
            nombre_producto TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1,
            precio REAL NOT NULL DEFAULT 0,
            descuento REAL DEFAULT 0,
            subtotal REAL NOT NULL DEFAULT 0,
            costo REAL DEFAULT 0,
            ganancia REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
            id SERIAL PRIMARY KEY,
            venta_id INTEGER REFERENCES ventas(id),
            cliente_id INTEGER REFERENCES clientes(id),
            total REAL NOT NULL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0,
            saldo REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS abonos_cobrar (
            id SERIAL PRIMARY KEY,
            cuenta_id INTEGER NOT NULL REFERENCES cuentas_por_cobrar(id),
            monto REAL NOT NULL,
            fecha DATE NOT NULL,
            metodo_pago TEXT DEFAULT 'EFECTIVO',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS gastos (
            id SERIAL PRIMARY KEY,
            concepto TEXT NOT NULL,
            categoria TEXT,
            fecha DATE NOT NULL,
            valor REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO',
            responsable TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS ingresos (
            id SERIAL PRIMARY KEY,
            concepto TEXT NOT NULL,
            categoria TEXT,
            fecha DATE NOT NULL,
            valor REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO',
            responsable TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS capital (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            valor REAL NOT NULL DEFAULT 0,
            fecha DATE NOT NULL,
            observaciones TEXT,
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inversiones (
            id SERIAL PRIMARY KEY,
            inversionista TEXT NOT NULL,
            monto REAL NOT NULL DEFAULT 0,
            fecha DATE NOT NULL,
            objetivo TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVA',
            retorno REAL DEFAULT 0,
            observaciones TEXT,
            codigo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS distribuciones (
            id SERIAL PRIMARY KEY,
            periodo_inicio DATE,
            periodo_fin DATE,
            utilidad_neta REAL DEFAULT 0,
            fecha_distribucion DATE,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS distribucion_detalles (
            id SERIAL PRIMARY KEY,
            distribucion_id INTEGER NOT NULL REFERENCES distribuciones(id) ON DELETE CASCADE,
            socio_id INTEGER NOT NULL REFERENCES socios(id),
            porcentaje REAL DEFAULT 0,
            monto REAL DEFAULT 0,
            pagado REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS comisiones (
            id SERIAL PRIMARY KEY,
            vendedor_id INTEGER NOT NULL REFERENCES vendedores(id),
            venta_id INTEGER REFERENCES ventas(id),
            porcentaje REAL DEFAULT 0,
            monto REAL DEFAULT 0,
            pagado REAL DEFAULT 0,
            pendiente REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
    else:
        cur = conn.cursor()
        cur.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT NOT NULL,
            email TEXT,
            rol TEXT NOT NULL DEFAULT 'VENDEDOR',
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            debe_cambiar_contrasena INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            descripcion TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            categoria_id INTEGER,
            marca TEXT,
            precio_compra REAL NOT NULL DEFAULT 0,
            precio_venta REAL NOT NULL DEFAULT 0,
            margen REAL DEFAULT 0,
            imagen TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        );
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, email TEXT, telefono TEXT, direccion TEXT,
            documento TEXT, estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, email TEXT, telefono TEXT, direccion TEXT,
            documento TEXT, estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER,
            nombre TEXT NOT NULL, email TEXT, telefono TEXT,
            porcentaje_comision REAL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL, porcentaje REAL NOT NULL DEFAULT 0,
            capital_aportado REAL DEFAULT 0, fecha_ingreso DATE,
            estado TEXT NOT NULL DEFAULT 'ACTIVO',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT, proveedor_id INTEGER,
            fecha DATE NOT NULL, total REAL NOT NULL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0, saldo REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO', observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        );
        CREATE TABLE IF NOT EXISTS compra_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, compra_id INTEGER NOT NULL,
            producto_id INTEGER, nombre_producto TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1, precio_unitario REAL NOT NULL DEFAULT 0,
            subtotal REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER,
            vendedor_id INTEGER, fecha DATE NOT NULL,
            total REAL NOT NULL DEFAULT 0, descuento REAL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0, saldo REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO', observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id)
        );
        CREATE TABLE IF NOT EXISTS venta_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL,
            producto_id INTEGER, nombre_producto TEXT NOT NULL,
            cantidad REAL NOT NULL DEFAULT 1, precio REAL NOT NULL DEFAULT 0,
            descuento REAL DEFAULT 0, subtotal REAL NOT NULL DEFAULT 0,
            costo REAL DEFAULT 0, ganancia REAL DEFAULT 0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );
        CREATE TABLE IF NOT EXISTS cuentas_por_cobrar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER,
            cliente_id INTEGER, total REAL NOT NULL DEFAULT 0,
            pagado REAL NOT NULL DEFAULT 0, saldo REAL NOT NULL DEFAULT 0,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
        CREATE TABLE IF NOT EXISTS abonos_cobrar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cuenta_id INTEGER NOT NULL,
            monto REAL NOT NULL, fecha DATE NOT NULL,
            metodo_pago TEXT DEFAULT 'EFECTIVO', observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas_por_cobrar(id)
        );
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT NOT NULL,
            categoria TEXT, fecha DATE NOT NULL, valor REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO', responsable TEXT,
            observaciones TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT NOT NULL,
            categoria TEXT, fecha DATE NOT NULL, valor REAL NOT NULL DEFAULT 0,
            metodo_pago TEXT DEFAULT 'EFECTIVO', responsable TEXT,
            observaciones TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS capital (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL,
            concepto TEXT NOT NULL, valor REAL NOT NULL DEFAULT 0,
            fecha DATE NOT NULL, observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inversiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, inversionista TEXT NOT NULL,
            monto REAL NOT NULL DEFAULT 0, fecha DATE NOT NULL, objetivo TEXT,
            estado TEXT NOT NULL DEFAULT 'ACTIVA', retorno REAL DEFAULT 0,
            observaciones TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS distribuciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, periodo_inicio DATE,
            periodo_fin DATE, utilidad_neta REAL DEFAULT 0,
            fecha_distribucion DATE,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            observaciones TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS distribucion_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, distribucion_id INTEGER NOT NULL,
            socio_id INTEGER NOT NULL, porcentaje REAL DEFAULT 0,
            monto REAL DEFAULT 0, pagado REAL DEFAULT 0,
            FOREIGN KEY (distribucion_id) REFERENCES distribuciones(id) ON DELETE CASCADE,
            FOREIGN KEY (socio_id) REFERENCES socios(id)
        );
        CREATE TABLE IF NOT EXISTS comisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT, vendedor_id INTEGER NOT NULL,
            venta_id INTEGER, porcentaje REAL DEFAULT 0, monto REAL DEFAULT 0,
            pagado REAL DEFAULT 0, pendiente REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id),
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        );
        ''')
        conn.commit()
    conn.close()


def seed_admin():
    from werkzeug.security import generate_password_hash
    conn = get_db()
    cur = conn.cursor()
    if _is_postgres():
        cur.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        existing = cur.fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, nombre, email, rol, debe_cambiar_contrasena) VALUES (%s, %s, %s, %s, %s, %s)",
                ('admin', generate_password_hash('admin123'), 'Administrador', 'admin@nibra.com', 'ADMIN', 1)
            )
        else:
            cur.execute("UPDATE usuarios SET debe_cambiar_contrasena = 1 WHERE username = 'admin'")
    else:
        existing = cur.execute("SELECT id FROM usuarios WHERE username = 'admin'").fetchone()
        if not existing:
            try:
                cur.execute(
                    "INSERT INTO usuarios (username, password_hash, nombre, email, rol, debe_cambiar_contrasena) VALUES (?, ?, ?, ?, ?, ?)",
                    ('admin', generate_password_hash('admin123'), 'Administrador', 'admin@nibra.com', 'ADMIN', 1)
                )
            except Exception:
                cur.execute(
                    "INSERT INTO usuarios (username, password_hash, nombre, email, rol) VALUES (?, ?, ?, ?, ?)",
                    ('admin', generate_password_hash('admin123'), 'Administrador', 'admin@nibra.com', 'ADMIN')
                )
        else:
            try:
                cur.execute("UPDATE usuarios SET debe_cambiar_contrasena = 1 WHERE username = 'admin'")
            except Exception:
                pass
    conn.commit()
    conn.close()
