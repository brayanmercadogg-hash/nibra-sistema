# NIBRA ERP - Sistema de Gestion Empresarial

Sistema ERP completo para administrar una empresa dedicada a productos de belleza y maquillaje.

## Tecnologias

- Python 3
- Flask
- SQLite
- Jinja2
- HTML/CSS/JavaScript
- Chart.js

## Instalacion

```bash
pip install -r requirements.txt
python app.py
```

La aplicacion estara disponible en `http://localhost:5000`

## Usuario Demo

- **Usuario:** admin
- **Contrasena:** admin123
- **Rol:** ADMIN

## Modulos

1. **Dashboard** - KPIs, graficas, ventas recientes
2. **Productos** - CRUD completo con imagenes
3. **Categorias** - Gestion de categorias
4. **Clientes** - CRUD con historial de compras
5. **Proveedores** - CRUD con historial de compras
6. **Compras** - Registro con multiples productos
7. **Ventas** - Registro con calculo automatico de costo/ganancia
8. **Cuentas por Cobrar** - Gestion de cobros con abonos
9. **Gastos** - Registro y filtros por fecha
10. **Ingresos** - Registro y filtros por fecha
11. **Capital** - Aportes, retiros y movimientos
12. **Socios** - CRUD con validacion de porcentajes
13. **Inversiones** - Registro y seguimiento
14. **Utilidades** - Calculo por periodo
15. **Distribucion de Ganancias** - Calculo por socio
16. **Vendedores** - CRUD con vinculo a usuarios
17. **Comisiones** - Calculo automatico por ventas
18. **Reportes** - 10 tipos con filtros y exportacion CSV
19. **Catalogo Publico** - Pagina publica de productos
20. **Usuarios** - Gestion con roles (ADMIN, SOCIO, VENDEDOR)

## Estructura

```
nibra-sistema/
├── app.py              # Aplicacion principal
├── config.py           # Configuracion
├── requirements.txt    # Dependencias
├── nibra.db           # Base de datos (se crea automaticamente)
├── database/          # Base de datos
├── routes/            # Rutas Flask
├── utils/             # Utilidades
├── templates/         # Plantillas HTML
└── static/            # Archivos estaticos
    ├── css/
    ├── js/
    └── img/
```

## Funcionalidades

- Autenticacion segura con hash de contrasenas
- Roles: ADMIN, SOCIO, VENDEDOR
- Interfaz responsive (movil y PC)
- Graficas de ventas y productos
- Exportacion CSV de reportes
- Calculos automaticos de ganancias y comisiones
- Validaciones de datos
- Base de datos SQLite normalizada
