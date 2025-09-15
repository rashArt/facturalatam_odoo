# Catálogo de Datos para Colombia (l10n_co_catalog)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Descripción

Este módulo proporciona catálogos de datos maestros necesarios para la localización de Colombia, incluyendo tipos de documentos, tipos de organizaciones, tipos de régimen, y más. Es esencial para implementar correctamente la facturación electrónica y el cumplimiento normativo colombiano en Odoo.

## Características Principales

### 📋 Catálogos Maestros Incluidos

- **Tipos de Documentos**: Catálogo completo de tipos de documentos según normativa DIAN
- **Tipos de Identificación**: Cédula, NIT, pasaporte, etc.
- **Formas de Pago**: Efectivo, transferencia, tarjeta de crédito, etc.
- **Métodos de Pago**: Según clasificación DIAN
- **Tipos de Organización**: Persona natural, jurídica, etc.
- **Tipos de Régimen**: Común, simplificado, etc.
- **Tipos de Responsabilidad**: O-13, O-15, etc.
- **Departamentos y Municipios**: División político-administrativa de Colombia
- **Unidades de Medida**: Según estándares colombianos
- **Tipos de Operación**: Venta, exportación, importación, etc.
- **Descuentos**: Tipos de descuentos permitidos
- **Discrepancias**: Para notas crédito y débito

### 🏢 Módulos Integrados

- **Contabilidad**: Configuración de impuestos y diarios contables
- **Recursos Humanos**: Configuración de nómina y contratos
- **Productos**: Configuración de productos y servicios
- **Configuración**: Panel de configuración centralizado

### 🔧 Funcionalidades Técnicas

- **Importación CSV**: Actualización masiva de datos desde archivos CSV
- **Secuencias de Diarios**: Numeración automática según normativa
- **Plantillas de Factura**: Configuración de plantillas para facturación electrónica
- **Establecimientos**: Gestión de establecimientos para facturación electrónica

## 🏗️ Estructura del Ecosistema

Este módulo forma parte de un **ecosistema completo de localización colombiana** para Odoo:

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

- `base` - Módulo base de Odoo
- `l10n_co` - Localización base de Colombia
- `account` - Contabilidad
- `update_from_csv` - Actualización desde CSV
- `journal_sequence` - Secuencias de diarios
- `hr_payroll_community` - Nómina comunitaria
- `hr_payroll_account_community` - Contabilización de nómina

### Pasos de Instalación

1. Descargar el módulo en la carpeta de addons de Odoo
2. Actualizar la lista de aplicaciones en Odoo
3. Buscar "Catálogo de Datos para Colombia"
4. Hacer clic en "Instalar"

## Configuración

### Configuración Inicial

Después de la instalación, vaya a:

1. **Configuración → Ajustes → Localización Colombiana**
   - Configure los parámetros básicos de la empresa
   - Establezca el tipo de régimen fiscal
   - Configure los establecimientos EDI

2. **Contabilidad → Configuración → Diarios**
   - Verifique la configuración de secuencias automáticas
   - Configure los prefijos según su necesidad

3. **Contabilidad → Configuración → Impuestos**
   - Revise la configuración de impuestos colombianos
   - Ajuste las tasas según sea necesario

### Configuración de Nómina

Si utiliza el módulo de nómina:

1. **Nómina → Configuración → Tipos de Contrato**
   - Configure los tipos de contrato según la legislación colombiana

2. **Nómina → Configuración → Empleados**
   - Configure la información fiscal de los empleados


## Desarrollo y Personalización

### Estructura del Módulo

```
l10n_co_catalog/
├── data/                 # Datos maestros en CSV y XML
├── models/               # Modelos Python
├── views/                # Vistas XML
├── security/             # Permisos y seguridad
├── static/               # Recursos estáticos
└── i18n/                 # Traducciones
```

## Soporte

Para soporte técnico y consultas:

- Crear un issue en el repositorio del proyecto
- Contactar al equipo de FacturaLatam en [soporte@facturalatam.com](mailto:soporte@facturalatam.com)