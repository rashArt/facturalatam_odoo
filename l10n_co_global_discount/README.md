# Descuentos Globales Colombia (l10n_co_global_discount)

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## Descripción

Módulo complementario gratuito que permite aplicar descuentos globales en órdenes de venta y facturas, adaptado específicamente para la localización colombiana. Optimizado para trabajar en conjunto con el ecosistema de facturación electrónica DIAN.

## Características Principales

### 💰 Tipos de Descuento Incluidos

- **Descuentos por Porcentaje**: Aplicar porcentaje sobre el subtotal de la orden o factura
- **Descuentos por Valor Fijo**: Valor específico independiente del total
- **Descuentos Automáticos**: Configuración de descuentos por defecto
- **Descuentos Manuales**: Aplicación específica según necesidad

### 📋 Documentos Soportados

- **Órdenes de Venta**: Descuentos antes de confirmar la orden
- **Facturas de Cliente**: Descuentos en facturación directa
- **Facturas de Proveedor**: Manejo de descuentos recibidos
- **Notas de Crédito**: Ajustes y correcciones con descuentos

### 🔧 Funcionalidades Técnicas

- **Cálculo Automático**: Recálculo de impuestos según normativa colombiana
- **Integración DIAN**: Compatible con facturación electrónica
- **Reversión Sencilla**: Quitar descuentos fácilmente
- **Totales en Tiempo Real**: Actualización automática de montos
- **Configuración Centralizada**: Panel de configuración unificado
- **Productos de Descuento**: Manejo automático de líneas de descuento

### 🏢 Módulos Integrados

- **Ventas**: Integración completa con órdenes de venta
- **Contabilidad**: Cálculo automático de impuestos
- **Configuración**: Panel de configuración centralizado
- **Facturación Electrónica**: Compatible con módulos EDI

## 🏗️ Estructura del Ecosistema

Este módulo forma parte del **ecosistema completo de localización colombiana** para Odoo:

```
🇨🇴 Localización Colombia - Ecosistema Completo
├── 🆓 l10n_co_catalog
│   ├── Catálogos maestros DIAN
│   ├── Tipos de documentos
│   └── Departamentos y municipios
├── 💰 l10n_co_edi_electronic_invoice
│   ├── Facturación electrónica DIAN
│   └── Integración con webservices
├── 🆓 l10n_co_global_discount
│   ├── Gestión de descuentos
├── 🆓 l10n_co_layout_custom
│   └── Plantillas PDF profesionales
└── 🆓 l10n_co_import_electronic_invoice
    └── Importación XML facturas
```

## Instalación

### Requisitos Previos

Este módulo requiere los siguientes módulos base:

- `sale` - Ventas
- `sale_management` - Gestión de ventas
- `account` - Contabilidad
- `l10n_co_catalog` - Catálogos maestros Colombia

### Pasos de Instalación

1. Descargar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones en Odoo
3. Buscar "Descuentos Globales Colombia"
4. Hacer clic en "Instalar"

## Configuración

### Configuración Inicial

Después de la instalación, vaya a:

1. **Configuración → Ajustes → Ventas**
   - Active "Descuentos Globales Colombia"
   - Seleccione producto de descuento predeterminado
   - Configure descuentos por defecto si es necesario

2. **Ventas → Configuración → Productos**
   - Verifique la configuración del producto de descuento
   - Configure categorías de descuento si es necesario

3. **Contabilidad → Configuración → Impuestos**
   - Revise la configuración de impuestos para descuentos
   - Ajuste las cuentas contables según sea necesario

### Configuración de Uso

En órdenes de venta y facturas:

1. **Crear nuevo documento**
2. **Añadir productos normalmente**
3. **En sección "Descuento Global Colombia":**
   - Seleccionar tipo (Porcentaje o Fijo)
   - Ingresar cantidad del descuento
   - Hacer clic en "Aplicar Descuento"

## Desarrollo y Personalización

### Estructura del Módulo

```
l10n_co_global_discount/
├── data/                 # Productos de descuento por defecto
├── views/                # Vistas XML
├── security/             # Permisos y seguridad
└── static/               # Recursos estáticos
```

## Soporte

Para soporte técnico y consultas:

- Contactar al equipo de FacturaLatam en [soporte@facturalatam.com](mailto:soporte@facturalatam.com)
- Visitar [facturalatam.com](https://facturalatam.com) para documentación adicional