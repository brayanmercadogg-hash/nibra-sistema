# PROMPT.md — NIBRA Sistema de Gestión Empresarial

## INSTRUCCIÓN PRINCIPAL

Trabaja directamente sobre el proyecto actual de NIBRA.

Tu objetivo es revisar, corregir, completar y dejar el sistema funcional, coherente, seguro y preparado para producción.

NO me hagas preguntas innecesarias.
NO esperes confirmación para continuar.
NO te limites a decirme qué está mal: corrígelo directamente.
NO reemplaces la arquitectura existente innecesariamente.
NO elimines funcionalidades que ya funcionan.

Antes de modificar algo importante, analiza cómo está implementado actualmente para evitar romper otras partes del sistema.

Después de cada modificación importante, vuelve a probar el sistema.

---

# 1. OBJETIVO DEL SISTEMA

NIBRA es un sistema de gestión empresarial para administrar la operación de la empresa.

Debe permitir administrar:

- productos
- categorías
- clientes
- proveedores
- ventas
- compras
- ingresos
- gastos
- capital
- socios
- inversiones
- cuentas por cobrar
- comisiones
- movimientos financieros
- reportes
- dashboard
- catálogo público
- usuarios
- roles y permisos

El sistema debe ser práctico para una pequeña empresa y funcionar correctamente desde computadora y celular.

La interfaz debe estar completamente en español.

La moneda utilizada es COP.

---

# 2. REGLA FUNDAMENTAL

No consideres que una funcionalidad está terminada solamente porque la página carga.

Una funcionalidad se considera terminada únicamente cuando:

1. La ruta funciona.
2. La interfaz funciona.
3. El formulario funciona.
4. La validación funciona.
5. Los datos se guardan correctamente.
6. Los datos pueden consultarse.
7. Los datos pueden editarse cuando corresponda.
8. Los datos pueden eliminarse cuando corresponda.
9. La base de datos mantiene la integridad.
10. No genera errores en Flask.
11. No genera errores JavaScript.
12. Los cálculos son correctos.
13. Los permisos son respetados.
14. La interfaz funciona correctamente en móvil.

---

# 3. PRIMERA ETAPA — ANALIZAR EL PROYECTO

Antes de modificar código:

- revisa la estructura completa del proyecto;
- revisa todos los archivos Python;
- revisa todas las rutas;
- revisa templates;
- revisa CSS;
- revisa JavaScript;
- revisa base de datos;
- revisa configuración;
- revisa requirements.txt;
- revisa README;
- identifica funcionalidades incompletas;
- identifica código duplicado;
- identifica código muerto;
- identifica rutas sin implementar;
- identifica formularios incompletos;
- identifica errores de arquitectura.

No cambies la estructura innecesariamente.

Mantén la estructura actual del proyecto siempre que sea viable.

---

# 4. SEGUNDA ETAPA — EJECUTAR EL SISTEMA

Ejecuta el proyecto.

Comprueba que Flask inicie correctamente.

Comprueba que no existan errores de importación.

Comprueba que no existan errores de sintaxis.

Ejecuta también:

python -m py_compile app.py config.py database/db.py routes/*.py utils/*.py

Si existen más módulos Python, inclúyelos en la comprobación.

Corrige cualquier error encontrado.

---

# 5. TERCERA ETAPA — REVISAR TODAS LAS RUTAS

Obtén todas las rutas registradas en Flask.

Comprueba cada ruta.

Busca especialmente:

- 200
- 201
- 302
- 400
- 401
- 403
- 404
- 405
- 409
- 422
- 500

Los errores 404, 405 y 500 deben investigarse.

No ignores errores simplemente porque una página principal funcione.

Si una ruta no debería existir, determina si es un enlace incorrecto o una funcionalidad faltante.

---

# 6. CUARTA ETAPA — AUTENTICACIÓN

Revisa completamente el sistema de autenticación.

Debe funcionar:

- login correcto;
- login incorrecto;
- logout;
- sesión;
- protección de rutas;
- acceso sin autenticación;
- expiración de sesión cuando corresponda;
- mensajes de error;
- redirecciones.

Comprueba que un usuario no autenticado no pueda entrar directamente a rutas protegidas.

Comprueba que un usuario con permisos insuficientes no pueda acceder a funciones administrativas.

Nunca expongas contraseñas ni secretos en el frontend.

---

# 7. ROLES Y PERMISOS

Revisa todos los roles existentes.

Comprueba que cada rol pueda acceder únicamente a las funciones correspondientes.

No confíes únicamente en ocultar botones del frontend.

Los permisos deben comprobarse también en backend.

Prueba acceso directo mediante URL.

Un usuario sin permiso administrativo no debe poder acceder simplemente escribiendo manualmente una URL administrativa.

---

# 8. IDENTIFICADORES Y CÓDIGOS AUTOMÁTICOS

ESTA ES UNA REGLA OBLIGATORIA.

El usuario NO debe tener que introducir manualmente identificadores internos.

Revisa todos los formularios.

Identifica campos como:

- ID
- código
- código de producto
- número de venta
- número de compra
- número de factura
- código de cliente
- código de proveedor
- código de inversión
- código de capital
- código de movimiento
- cualquier identificador interno

Cuando corresponda, deben generarse automáticamente.

## PRODUCTOS

El usuario debe introducir solamente información del producto, por ejemplo:

- nombre
- categoría
- descripción
- precio
- costo
- imagen
- estado
- demás información necesaria

NO debe introducir manualmente:

- ID
- código interno

Si NIBRA necesita un código visible, generarlo automáticamente.

Ejemplo:

NIB-PROD-00001
NIB-PROD-00002
NIB-PROD-00003

El formato debe ser consistente.

## OTROS REGISTROS

Aplica el mismo principio donde corresponda.

Ejemplos:

NIB-CLI-00001
NIB-PROV-00001
NIB-VTA-00001
NIB-CMP-00001
NIB-MOV-00001

No es obligatorio utilizar exactamente estos formatos si la estructura existente permite una solución mejor.

Lo importante es:

- generación automática;
- unicidad;
- consistencia;
- ausencia de duplicados;
- persistencia;
- integridad referencial.

## IMPORTANTE SOBRE LA BASE DE DATOS

No reemplaces innecesariamente los IDs internos de la base de datos.

Es preferible mantener:

id = identificador interno
codigo = identificador visible/comercial

Ejemplo:

id: 27
codigo: NIB-PROD-00027

Las relaciones internas deben utilizar las claves correspondientes de la base de datos.

## PRUEBA DE IDENTIFICADORES

Después de implementarlos:

1. Crear registro.
2. Verificar generación automática.
3. Crear segundo registro.
4. Verificar que el código sea diferente.
5. Editar registro.
6. Confirmar que conserve su código.
7. Eliminar registro.
8. Crear otro registro.
9. Confirmar que no existan conflictos.
10. Revisar directamente la base de datos.

---

# 9. PRODUCTOS

Revisar completamente el módulo de productos.

Debe funcionar:

- crear;
- listar;
- buscar;
- filtrar;
- editar;
- eliminar;
- activar/desactivar;
- categorías;
- precios;
- costos;
- descripción;
- imágenes cuando existan;
- código automático.

Validar:

- campos obligatorios;
- valores numéricos;
- precios negativos;
- datos vacíos;
- duplicados.

No permitir datos inválidos.

---

# 10. CATEGORÍAS

Revisar:

- crear;
- listar;
- editar;
- eliminar;
- relación con productos.

No permitir eliminar una categoría si existen dependencias sin resolver, a menos que la lógica existente permita hacerlo de forma segura.

---

# 11. CLIENTES

Revisar completamente el CRUD.

Debe permitir:

- crear;
- consultar;
- editar;
- eliminar cuando corresponda;
- buscar;
- consultar cuentas pendientes;
- historial de compras cuando corresponda.

Los identificadores deben generarse automáticamente.

---

# 12. PROVEEDORES

Revisar completamente:

- crear;
- consultar;
- editar;
- eliminar;
- buscar;
- historial de compras.

Los identificadores deben generarse automáticamente.

---

# 13. VENTAS

Revisar completamente el módulo de ventas.

Debe permitir registrar correctamente:

- cliente;
- productos;
- cantidades;
- precios;
- subtotal;
- descuentos cuando existan;
- total;
- forma de pago;
- estado;
- fecha;
- observaciones.

La venta debe guardar correctamente sus detalles.

Evitar errores de redondeo.

Utilizar valores monetarios de forma segura.

---

# 14. COMPRAS

Revisar:

- proveedor;
- productos;
- cantidades;
- costo;
- subtotal;
- total;
- fecha;
- estado;
- observaciones.

Comprobar que la información financiera se registre correctamente.

---

# 15. INGRESOS

Revisar:

- creación;
- edición;
- consulta;
- eliminación cuando corresponda;
- categorías;
- monto;
- fecha;
- descripción;
- método de pago.

Comprobar que afecte correctamente los indicadores financieros cuando corresponda.

---

# 16. GASTOS

Revisar:

- creación;
- edición;
- consulta;
- eliminación cuando corresponda;
- categorías;
- monto;
- fecha;
- descripción;
- método de pago.

Validar que los gastos no generen valores negativos incorrectos.

---

# 17. CAPITAL

Revisar completamente el módulo de capital.

Debe distinguir correctamente entre:

- capital inicial;
- aportes;
- retiros;
- movimientos correspondientes.

Los movimientos deben quedar registrados.

No confundir capital aportado con utilidad.

---

# 18. SOCIOS

Revisar:

- socios;
- porcentajes;
- aportes;
- participación;
- información relacionada.

Los porcentajes deben validarse.

No permitir porcentajes imposibles.

Cuando corresponda, la suma de participaciones debe validarse según las reglas del sistema.

---

# 19. INVERSIONES

Revisar:

- creación;
- monto;
- inversionista;
- fecha;
- estado;
- devolución;
- rentabilidad cuando corresponda.

No mezclar automáticamente inversión con utilidad.

Mantener separados:

- capital;
- inversión;
- ingresos;
- gastos;
- utilidad.

---

# 20. CUENTAS POR COBRAR

Revisar:

- creación de deuda;
- cliente;
- monto;
- pagos;
- saldo pendiente;
- estado;
- historial.

Comprobar:

saldo pendiente = deuda original - pagos realizados

No permitir que el saldo quede incorrectamente negativo salvo que el sistema contemple explícitamente pagos excedentes.

---

# 21. COMISIONES

Revisar:

- vendedor;
- venta relacionada;
- porcentaje;
- valor;
- estado;
- pago.

Comprobar que las comisiones no se calculen dos veces.

---

# 22. DASHBOARD

Revisar todos los KPIs.

Los valores mostrados deben coincidir con la base de datos.

Revisar:

- ventas;
- ingresos;
- gastos;
- compras;
- cuentas por cobrar;
- capital;
- utilidad;
- movimientos;
- indicadores.

No mostrar datos ficticios o valores hardcodeados.

Si un gráfico no tiene datos, mostrar correctamente un estado vacío.

---

# 23. CÁLCULOS FINANCIEROS

Revisar cuidadosamente todos los cálculos.

Especialmente:

- ingresos;
- gastos;
- ventas;
- compras;
- capital;
- utilidad;
- cuentas por cobrar;
- comisiones.

No asumir que:

dinero recibido = utilidad

Separar correctamente:

- ingresos;
- costos;
- gastos;
- capital;
- inversiones;
- cuentas por cobrar;
- utilidad.

Todos los cálculos deben utilizar los datos reales de la base de datos.

---

# 24. BASE DE DATOS

Revisar:

- tablas;
- columnas;
- claves primarias;
- claves foráneas;
- restricciones;
- índices;
- relaciones;
- tipos de datos;
- valores NULL;
- duplicados.

No romper relaciones existentes.

Evitar eliminar columnas o tablas que estén siendo utilizadas.

Antes de cambiar el esquema, comprobar dependencias.

---

# 25. VALIDACIÓN DE DATOS

Todos los formularios deben validar:

- campos obligatorios;
- números;
- fechas;
- cantidades;
- precios;
- porcentajes;
- texto;
- valores negativos;
- duplicados.

La validación debe existir en backend.

El frontend puede mejorar la experiencia, pero nunca debe ser la única validación.

---

# 26. SEGURIDAD

Revisar:

- contraseñas;
- sesiones;
- secret key;
- autenticación;
- autorización;
- SQL injection;
- XSS;
- CSRF cuando corresponda;
- validación de archivos;
- subida de imágenes;
- acceso directo a rutas;
- información sensible;
- variables de entorno.

No dejar:

- contraseñas reales;
- claves secretas;
- tokens;
- credenciales;
- datos sensibles

directamente expuestos en el código.

Si existen credenciales de desarrollo, documentar correctamente cómo configurarlas sin exponer secretos reales.

---

# 27. TEMPLATES

Revisar todos los templates.

Buscar:

- variables inexistentes;
- enlaces incorrectos;
- formularios incorrectos;
- campos que no corresponden al backend;
- botones que no funcionan;
- rutas equivocadas;
- errores Jinja.

Todo enlace del menú debe llevar a una ruta válida.

---

# 28. JAVASCRIPT

Revisar todos los archivos JS.

Buscar:

- errores de consola;
- selectores inexistentes;
- funciones inexistentes;
- endpoints incorrectos;
- respuestas mal procesadas;
- formularios que no envían datos;
- eventos que no funcionan.

No dejar errores JavaScript innecesarios.

---

# 29. CSS Y RESPONSIVE

Revisar el diseño en:

- celular;
- tablet;
- escritorio.

Especialmente:

- menú lateral;
- tablas;
- formularios;
- botones;
- tarjetas;
- dashboard;
- catálogo;
- modales.

Evitar:

- contenido cortado;
- scroll horizontal innecesario;
- botones fuera de pantalla;
- textos superpuestos;
- tablas inutilizables en móvil.

Mantener el diseño profesional de NIBRA.

---

# 30. CATÁLOGO PÚBLICO

Revisar:

- acceso público;
- productos;
- categorías;
- precios;
- imágenes;
- disponibilidad;
- diseño;
- responsive;
- enlaces.

El catálogo no debe requerir autenticación si está diseñado como catálogo público.

No mostrar información administrativa o financiera.

---

# 31. MANEJO DE ERRORES

El sistema debe manejar correctamente:

- registro inexistente;
- formulario inválido;
- datos duplicados;
- errores de base de datos;
- acceso no autorizado;
- ruta inexistente;
- sesión inválida.

Evitar mostrar trazas internas al usuario final en producción.

Crear páginas de error apropiadas cuando corresponda.

---

# 32. DATOS DE PRUEBA

Cuando sea necesario realizar pruebas:

Utiliza datos claramente identificables como:

TEST
PRUEBA
DEMO

No mezcles datos de prueba con información real de NIBRA.

Si creas datos temporales, elimínalos después de las pruebas cuando sea seguro hacerlo.

---

# 33. PRUEBAS CRUD

Para cada módulo CRUD realizar:

CREAR
↓
CONSULTAR
↓
EDITAR
↓
VOLVER A CONSULTAR
↓
ELIMINAR
↓
VERIFICAR

Comprobar tanto la interfaz como la base de datos.

---

# 34. PRUEBAS DE INTEGRACIÓN

No probar únicamente módulos aislados.

Comprobar relaciones:

Producto → Venta
Producto → Compra
Cliente → Venta
Cliente → Cuenta por cobrar
Proveedor → Compra
Venta → Comisión
Capital → Movimiento
Socio → Participación

Comprobar que las operaciones relacionadas no generen inconsistencias.

---

# 35. PRUEBAS DE REGRESIÓN

Después de corregir un error:

1. vuelve a ejecutar el proyecto;
2. prueba la funcionalidad corregida;
3. prueba las funcionalidades relacionadas;
4. revisa los logs;
5. verifica la base de datos.

Una corrección no debe romper funcionalidades existentes.

---

# 36. LIMPIEZA DEL PROYECTO

Revisar:

- imports innecesarios;
- código duplicado;
- archivos innecesarios;
- funciones sin utilizar;
- comentarios obsoletos;
- rutas duplicadas;
- dependencias innecesarias.

No eliminar archivos sin comprobar primero que no sean utilizados.

---

# 37. FAVICON

Si existe un error como:

GET /favicon.ico 404

corrígelo agregando un favicon apropiado y configurándolo correctamente.

No considerarlo un error crítico, pero sí corregirlo como parte del acabado final.

---

# 38. RENDIMIENTO

Revisar problemas evidentes de rendimiento:

- consultas repetidas;
- consultas innecesarias;
- carga excesiva de datos;
- imágenes demasiado grandes;
- JavaScript innecesario;
- consultas sin índices cuando realmente sean necesarios.

No realizar optimizaciones complejas innecesarias.

Priorizar estabilidad y claridad.

---

# 39. PRODUCCIÓN

Antes de considerar el proyecto listo para producción:

Revisar:

- DEBUG;
- secret key;
- configuración;
- variables de entorno;
- credenciales;
- base de datos;
- manejo de errores;
- sesiones;
- seguridad;
- archivos estáticos;
- host;
- puerto;
- dependencias.

El servidor de desarrollo de Flask NO debe considerarse una configuración final de producción.

---

# 40. NO HACER

NO:

- pedir confirmación constantemente;
- detenerte ante un error solucionable;
- inventar funcionalidades;
- eliminar funcionalidades sin motivo;
- cambiar la arquitectura porque sí;
- cambiar nombres de tablas sin necesidad;
- romper la base de datos;
- introducir IDs manuales;
- dejar códigos duplicables;
- dejar errores conocidos sin documentar;
- ocultar errores simplemente para que la página parezca funcionar.

---

# 41. ORDEN DE TRABAJO

Trabaja en este orden:

1. Analizar proyecto.
2. Revisar base de datos.
3. Ejecutar proyecto.
4. Revisar rutas.
5. Revisar autenticación.
6. Revisar permisos.
7. Revisar identificadores automáticos.
8. Revisar CRUD.
9. Revisar ventas.
10. Revisar compras.
11. Revisar ingresos.
12. Revisar gastos.
13. Revisar capital.
14. Revisar socios.
15. Revisar inversiones.
16. Revisar cuentas por cobrar.
17. Revisar comisiones.
18. Revisar dashboard.
19. Revisar catálogo.
20. Revisar frontend.
21. Revisar responsive.
22. Revisar seguridad.
23. Corregir errores.
24. Ejecutar pruebas nuevamente.
25. Revisar producción.
26. Generar informe final.

---

# 42. CRITERIO DE FINALIZACIÓN

No declares el proyecto terminado solamente porque Flask arranque.

Declara:

LISTO

únicamente cuando hayas realizado todas las comprobaciones posibles y hayas corregido los problemas encontrados.

Si existe algo que realmente no pueda probarse automáticamente, indícalo claramente.

---

# 43. INFORME FINAL

Al terminar, genera un informe con:

## ESTADO GENERAL

LISTO

o

REQUIERE CORRECCIONES

## ERRORES ENCONTRADOS

Lista de errores encontrados.

## ERRORES CORREGIDOS

Lista de correcciones realizadas.

## FUNCIONALIDADES PROBADAS

Lista de módulos probados.

## PRUEBAS DE BASE DE DATOS

Indicar qué se verificó.

## PRUEBAS DE SEGURIDAD

Indicar qué se verificó.

## PRUEBAS RESPONSIVE

Indicar qué se verificó.

## IDENTIFICADORES AUTOMÁTICOS

Indicar qué módulos fueron corregidos.

## ERRORES PENDIENTES

Lista únicamente de problemas que realmente no pudieron solucionarse.

## RECOMENDACIONES PARA PRODUCCIÓN

Lista de recomendaciones finales.

---

# 44. INSTRUCCIÓN FINAL

Trabaja de forma autónoma.

Analiza.

Ejecuta.

Prueba.

Encuentra errores.

Corrige.

Vuelve a probar.

Revisa la base de datos.

Comprueba las integraciones.

Revisa seguridad.

Revisa interfaz.

Repite el proceso hasta obtener el sistema más estable posible.

NO me preguntes qué hacer después.

Si encuentras un problema solucionable, soluciónalo directamente.

El objetivo final es:

NIBRA funcionando correctamente, con datos coherentes, identificadores automáticos, módulos integrados, interfaz profesional, seguridad básica adecuada y preparado para pasar posteriormente a producción.
