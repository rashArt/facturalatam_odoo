# Descuentos Globales Colombia

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-purple.svg)](https://www.odoo.com/)

## 🎯 Descripción

Módulo **complementario gratuito** que permite aplicar descuentos globales en órdenes de venta y facturas, adaptado específicamente para la localización colombiana. Optimizado para trabajar en conjunto con el ecosistema de facturación electrónica DIAN.


## 🚀 Funcionalidades

### 💰 Tipos de Descuento

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **Porcentaje** | Descuento como % del subtotal | 10% sobre $100.000 = $10.000 |
| **Valor Fijo** | Descuento por valor específico | $5.000 fijo independiente del total |

### 📋 Documentos Soportados

- **Órdenes de Venta** - Aplicar descuentos antes de confirmar
- **Facturas de Cliente** - Descuentos en facturación directa
- **Facturas de Proveedor** - Manejo de descuentos recibidos
- **Notas de Crédito** - Ajustes y correcciones

#### Cálculos Automáticos
- 🧮 **Recálculo de Impuestos** - Automático según normativa colombiana
- 📊 **Totales Actualizados** - En tiempo real
- 🔄 **Reversión Sencilla** - Quitar descuentos fácilmente

Este módulo forma parte del **ecosistema completo de localización para Colombia**:

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

## 🛠️ Instalación

### Prerequisitos

| Módulo | Versión | Estado |
|--------|---------|--------|
| **l10n_co_catalog** | 18.0+ | ✅ Requerido |
| **sale_management** | 18.0+ | ✅ Requerido |
| **account** | 18.0+ | ✅ Automático |


### Configuración Inicial

1. **Ir a Configuración → Ajustes → Ventas**
2. **Activar "Descuentos Globales Colombia"**
3. **Seleccionar producto de descuento predeterminado**
4. **Guardar configuración**

## 📖 Uso

### 🛒 En Órdenes de Venta

1. **Crear nueva orden de venta**
2. **Añadir productos normalmente**
3. **En sección "Descuento Global Colombia":**
   - Seleccionar tipo (Porcentaje o Fijo)
   - Ingresar cantidad del descuento
   - Hacer clic en "Aplicar Descuento"
4. **El sistema automáticamente:**
   - Crea línea de descuento
   - Recalcula impuestos
   - Actualiza totales

### 🧾 En Facturas

1. **Crear nueva factura**
2. **Añadir líneas de productos**
3. **Aplicar descuento global igual que en ventas**
4. **El descuento se refleja correctamente en:**
   - Representación impresa
   - XML de facturación electrónica (si tiene módulo comercial)
   - Contabilización

---

## 🔧 Desarrollo y Personalización

### Estructura del Módulo

```
l10n_co_global_discount/
├── models/
│   ├── sale_order.py          # Extensión órdenes de venta
│   ├── account_move.py        # Extensión facturas
│   ├── res_config_settings.py # Configuración
│   └── res_company.py         # Configuración por empresa
├── views/
│   ├── sale_order_views.xml   # Vistas de ventas
│   ├── account_move_views.xml # Vistas de facturas
│   └── res_config_settings_views.xml
├── data/
│   └── default_product_discount.xml
└── security/
    └── ir.model.access.csv
```

### 👨‍💻 Desarrollador
- **Empresa**: FacturaLatam
- **Website**: https://facturalatam.com
- **Email**: soporte@facturalatam.com

## 📄 Licencia

Licenciado bajo **LGPL-3** - Libre para uso comercial y modificación.