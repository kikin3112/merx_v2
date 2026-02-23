# Project

Sistema ERP con optimización de experiencia de usuario mediante micro-interacciones, feedback inmediato y unificación de módulos fragmentados. El proyecto busca transformar un ERP tradicional en una herramienta emocionante y eficiente que elimina la navegación entre múltiples módulos para operaciones simples.

## Stack

- **Frontend**: React con Zustand para gestión de estado
- **Comunicación en tiempo real**: Server-Sent Events (SSE) para actualizaciones del dashboard
- **Rendimiento**: react-window para virtualización de listas masivas
- **Animaciones**: React Spring o Framer Motion para micro-interacciones
- **Paginación**: Cursor-based pagination para inventarios masivos
- **Arquitectura**: Módulos compuestos unificados (producto+inventario, factura+cliente, etc.)

## Commands

```bash
# Instalación de dependencias
npm install

# Inicio de desarrollo
npm run dev

# Construcción para producción
npm run build

# Ejecución de pruebas
npm test

# Análisis de rendimiento
npm run analyze
```

## Architecture

**Capa de Presentación**: Componentes React con micro-interacciones y animaciones físicamente realistas usando React Spring. Cada módulo es un compuesto unificado que integra todas las acciones relacionadas con una entidad (ej. Producto + Inventario + Gestión de Stock).

**Estado Global**: Zustand con estado normalizado por IDs para evitar duplicación y asegurar consistencia entre módulos. Stores específicos para dashboard, productos, inventarios, facturación, etc.

**Comunicación en Tiempo Real**: SSE para actualizaciones instantáneas del dashboard de facturación, eliminando la necesidad de polling o recargas manuales.

**Optimización de Rendimiento**: Virtualización de listas para manejar 100k+ filas sin degradar el rendimiento, paginación basada en cursores para evitar saltos de registros, y React.memo con selectores eficientes.

**Navegación Contextual**: Sistema de routing inteligente que entiende el contexto del usuario y sugiere la siguiente acción natural, eliminando el "context switching" entre módulos.

**Flujos Integrados**: Módulos compuestos donde crear un producto incluye automáticamente la gestión de su inventario inicial, o procesar una factura incluye verificación de stock y actualización automática.
