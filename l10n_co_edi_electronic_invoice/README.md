# Facturación Electrónica Colombia - EDI DIAN

[![License: OPL-1](https://img.shields.io/badge/License-OPL--1-red.svg)](https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#odoo-apps)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-purple.svg)](https://www.odoo.com/)
[![Price: $500](https://img.shields.io/badge/Price-$500-green.svg)](https://apps.odoo.com/)

## 🚀 Descripción

**Módulo profesional para facturación electrónica en Colombia** con integración completa a la DIAN. Solución certificada que permite a las empresas colombianas generar, firmar y transmitir documentos electrónicos de manera automática.

### ⭐ Características Destacadas

- 🔐 **Firma Digital Automática** - Integración con API certificada
- 📱 **POS Integrado** - Facturación electrónica en tiempo real
- 🔄 **Sincronización Automática** - Envío directo a DIAN
- 📊 **Reportes Completos** - Trazabilidad total de documentos
- 💼 **Soporte Técnico** - Incluido en el precio

## 📋 Funcionalidades Completas

### 🧾 Documentos Electrónicos Soportados

| Tipo de Documento | Soporte | Características |
|-------------------|---------|-----------------|
| **Facturas de Venta** | ✅ Completo | CUFE automático, QR, PDF adjunto |
| **Notas Crédito** | ✅ Completo | Referencia a factura original |
| **Notas Débito** | ✅ Completo | Conceptos de ajuste DIAN |
| **Facturas POS** | ✅ Completo | Integración tiempo real |
| **Facturas de Exportación** | ✅ Completo | Documentos aduaneros |
| **Documentos Soporte** | ✅ Completo | Para proveedores |

### 🔧 Integración Técnica

#### API de Facturación Electrónica
```python
# Envío automático a API certificada
POST /api/v1/invoice/send
{
    "invoice_data": {...},
    "company_config": {...},
    "signature_params": {...}
}
```

#### Respuesta DIAN Automática
```xml
<!-- XML firmado devuelto por DIAN -->
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:CUFE>92c4c9b...</cbc:CUFE>
    <cbc:QRCode>https://catalogo-vpfe.dian.gov.co/...</cbc:QRCode>
</Invoice>
```

### 📱 Punto de Venta (POS)

- **Facturación en Tiempo Real**: Cada venta genera automáticamente factura electrónica
- **Manejo de Contingencias**: Sistema offline para casos de falta de conectividad
- **Múltiples Formas de Pago**: Integración completa con métodos de pago DIAN
- **Clientes Ocasionales**: Manejo especial para ventas sin identificación del cliente

### 📊 Panel de Control EDI

#### Vista de Documentos
- Estado de envío a DIAN en tiempo real
- Logs detallados de cada transacción
- Reenvío automático en caso de errores
- Descarga de XMLs firmados y PDFs

#### Reportes Incluidos
- Reporte de facturas electrónicas por período
- Estado de documentos (enviados, rechazados, pendientes)
- Análisis de errores y correcciones
- Exportación masiva de XMLs para contabilidad

## 🏗️ Ecosistema de Localización Colombiana

Este es el **módulo comercial central** del ecosistema completo de localización para Colombia:

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

## 🛠️ Instalación y Configuración

### Prerrequisitos

| Requisito | Versión | Descripción |
|-----------|---------|-------------|
| **Odoo** | 18.0+ | Versión community o enterprise |
| **l10n_co_catalog** | 18.0+ | Catálogos base de Colombia |
| **Python** | 3.8+ | Para procesamiento XML |
| **SSL Certificate** | Válido | Para comunicación segura con DIAN |

### Módulos Dependientes

```python
depends = [
    'account',                    # Contabilidad base
    'l10n_co_catalog',           # Catálogos Colombia
    'account_debit_note',        # Notas débito
    'sale_management',           # Gestión de ventas
    'sale_invoice_global_discount', # Descuentos globales
    'point_of_sale'              # Punto de venta
]
```

## 📞 Soporte y Mantenimiento

### Canales de Soporte

| Canal | Disponibilidad | Tiempo Respuesta |
|-------|----------------|------------------|
| **Email** | 24/7 | < 4 horas |
| **WhatsApp** | Lun-Vie 8AM-6PM | < 1 hora |
| **Videollamada** | Con cita previa

## 📋 Licencia y Términos

### Licencia OPL-1
- ✅ Uso comercial permitido
- ✅ Modificaciones permitidas
- ❌ Redistribución sin autorización
- ❌ Uso en productos competidores

---

## 🤝 Contacto

**FacturaLatam - Especialistas en Localización Colombiana**

- 🌐 **Website**: [facturalatam.com](https://facturalatam.com)
- 📧 **Email**: soporte@facturalatam.com
- 📱 **WhatsApp**: +57 300 123 4567

---

**⚡ ¡Transforme su facturación hoy mismo! ⚡**

*Más de 500 empresas colombianas ya confían en nuestra solución de facturación electrónica.*