# Facturación Electrónica Colombia - DIAN (l10n_co_edi_electronic_invoice)

[![License: OPL-1](https://img.shields.io/badge/License-OPL--1-red.svg)](https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#odoo-apps)

## Descripción

Módulo profesional para facturación electrónica en Colombia con integración completa a la DIAN. Solución certificada que permite a las empresas colombianas generar, firmar y transmitir documentos electrónicos de manera automática según la resolución 000042 de 2020 de la DIAN.

## Características Principales

### 🧾 Documentos Electrónicos Soportados

- **Facturas de Venta**: Generación automática con CUFE, QR y PDF adjunto
- **Notas Crédito**: Referencia automática a factura original
- **Notas Débito**: Conceptos de ajuste según normativa DIAN
- **Facturas POS**: Integración en tiempo real con punto de venta
- **Facturas de Exportación**: Documentos aduaneros incluidos
- **Documentos Soporte**: Para registro de proveedores

### 🔧 Funcionalidades Técnicas

- **Firma Digital Automática**: Integración con API certificada
- **Transmisión DIAN**: Envío directo y obtención automática de CUFE
- **POS Integrado**: Facturación electrónica en tiempo real
- **Reportes EDI**: Trazabilidad completa de documentos
- **Configuración Automática**: Según resolución DIAN de la empresa
- **Manejo de Contingencias**: Documentos offline y reenvío automático
- **Panel de Control**: Estado de envío y logs detallados
- **Reenvío Automático**: En caso de errores de conectividad

### 🏢 Módulos Integrados

- **Contabilidad**: Generación automática de facturas electrónicas
- **Punto de Venta**: Facturación electrónica en tiempo real
- **Ventas**: Integración con órdenes de venta
- **Configuración**: Panel de configuración centralizado

## 🏗️ Estructura del Ecosistema

Este es el **módulo comercial central** del ecosistema completo de localización colombiana para Odoo:

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

- `account` - Contabilidad
- `l10n_co_catalog` - Catálogos maestros Colombia
- `account_debit_note` - Notas débito
- `sale_management` - Gestión de ventas
- `l10n_co_global_discount` - Descuentos globales
- `point_of_sale` - Punto de venta

### Pasos de Instalación

1. Descargar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones en Odoo
3. Buscar "Facturación Electrónica Colombia - DIAN"
4. Hacer clic en "Instalar"

## Configuración

### Configuración Inicial

Después de la instalación, vaya a:

1. **Configuración → Ajustes → Facturación Electrónica**
   - Configure los parámetros de conexión con la API
   - Establezca los certificados de firma digital
   - Configure la información de la empresa para DIAN

2. **Contabilidad → Configuración → Diarios**
   - Verifique la configuración de secuencias para documentos electrónicos
   - Configure los prefijos según su resolución DIAN

3. **Punto de Venta → Configuración → Punto de Venta**
   - Active la facturación electrónica para cada POS
   - Configure el manejo de contingencias

### Configuración de Establecimientos EDI

1. **Configuración → Establecimientos EDI**
   - Configure cada establecimiento autorizado por DIAN
   - Establezca rangos de numeración según resolución

### Estructura del Módulo

```
l10n_co_edi_electronic_invoice/
├── models/               # Modelos Python para EDI
├── views/                # Vistas XML
├── reports/              # Reportes de facturas electrónicas
├── security/             # Permisos y seguridad
├── static/               # Recursos estáticos
└── data/                 # Configuración inicial
```
## Soporte

Para soporte técnico y consultas:

- Contactar al equipo de FacturaLatam en [soporte@facturalatam.com](mailto:soporte@facturalatam.com)
- Visitar [facturalatam.com](https://facturalatam.com) para documentación adicional
