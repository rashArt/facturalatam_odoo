# Plantillas PDF Colombia - Representación Impresa DIAN (l10n_co_layout_custom)

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## Descripción

Módulo complementario gratuito que proporciona plantillas PDF personalizadas y profesionales para documentos de facturación electrónica en Colombia. Diseñado específicamente para cumplir con los requisitos de representación impresa establecidos por la DIAN según la resolución 000042 de 2020.

## Características Principales

### 🧾 Documentos Soportados

- **Facturas Electrónicas**: QR, CUFE, información fiscal completa
- **Notas Crédito**: Referencia clara a documento original
- **Notas Débito**: Conceptos de ajuste bien definidos
- **Facturas POS**: Formato optimizado para punto de venta
- **Documentos Soporte**: Para proveedores y terceros

### 🎨 Elementos de Diseño Incluidos

- **Información de Empresa**: Logo empresarial y datos de contacto organizados
- **Información DIAN**: Código QR, CUFE/CUDE, resolución y fechas de vigencia
- **Datos del Cliente**: Información completa con régimen fiscal y responsabilidades
- **Detalle de Productos**: Tabla optimizada con precios e impuestos claramente separados
- **Totales Destacados**: Fácil identificación de montos importantes

### 🔧 Funcionalidades Técnicas

- **Plantillas Profesionales**: Diseño elegante y moderno adaptado a normativa DIAN
- **Representación Impresa**: Cumple resolución 000042 de 2020 oficial
- **Código QR Optimizado**: Tamaño y posición óptimos para escaneo
- **CUFE/CUDE Visible**: Destacado y fácil de identificar
- **Branding Empresarial**: Logo y colores corporativos personalizables
- **Optimización de Impresión**: CSS print-friendly y responsive
- **Templates Modulares**: Fácil personalización y mantenimiento
- **Variables Configurables**: Colores, fuentes y espaciado

### 🏢 Módulos Integrados

- **Facturación Electrónica**: Compatible con módulos EDI
- **Contabilidad**: Integración con facturas y documentos contables
- **Reportes**: Sistema de reportes personalizado
- **Configuración**: Panel de configuración centralizado

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

- `l10n_co_catalog` - Catálogos maestros Colombia
- `l10n_co_edi_electronic_invoice` - Facturación electrónica DIAN

### Pasos de Instalación

1. Descargar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones en Odoo
3. Buscar "Plantillas PDF Colombia - Representación Impresa DIAN"
4. Hacer clic en "Instalar"

## Configuración

### Configuración Inicial

Después de la instalación, vaya a:

1. **Configuración → Ajustes → Configuración de Empresa**
   - Configure el logo empresarial
   - Establezca los colores corporativos
   - Configure la información de contacto

2. **Configuración → Reportes → Plantillas**
   - Verifique la configuración de plantillas PDF
   - Configure variables de diseño si es necesario

3. **Contabilidad → Configuración → Documentos**
   - Seleccione las plantillas PDF personalizadas
   - Configure el formato de impresión por defecto

### Configuración de Plantillas

Para personalizar las plantillas:

1. **Acceder a Configuración → Técnico → Reportes**
2. **Seleccionar la plantilla de factura**
3. **Modificar variables CSS según necesidades**
4. **Guardar y probar la impresión**

## Desarrollo y Personalización

### Estructura del Módulo

```
l10n_co_layout_custom/
├── data/                 # Configuración inicial
├── templates/            # Plantillas QWeb
├── static/               # CSS y recursos estáticos
└── data/                 # Reportes y layouts
```

## Soporte

Para soporte técnico y consultas:

- Contactar al equipo de FacturaLatam en [soporte@facturalatam.com](mailto:soporte@facturalatam.com)
- Visitar [facturalatam.com](https://facturalatam.com) para documentación adicional