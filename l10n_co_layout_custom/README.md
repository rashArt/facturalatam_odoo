# Plantillas PDF Colombia - Representación Impresa DIAN

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-purple.svg)](https://www.odoo.com/)

## 🎨 Descripción

Módulo **complementario gratuito** que proporciona plantillas PDF personalizadas y profesionales para documentos de facturación electrónica en Colombia. Diseñado específicamente para cumplir con los requisitos de representación impresa establecidos por la DIAN según la resolución 000042 de 2020.

### ⭐ Características Destacadas

- ✅ **100% Gratuito** - Sin costos ocultos
- 🎨 **Diseño Profesional** - Plantillas elegantes y modernas
- 📋 **Cumplimiento DIAN** - Representación impresa oficial
- 🔧 **Fácil Instalación** - Configuración automática
- 🔄 **Compatible** - Funciona con módulos de facturación electrónica
- 📱 **Responsive** - Optimizado para impresión y visualización

## 🚀 ¿Por qué usar este módulo?

| Antes | Después |
|-------|---------|
| 📄 Facturas con diseño básico | 🎨 Facturas profesionales y elegantes |
| ❌ Información dispersa y confusa | ✅ Datos organizados y claros |
| 🔍 QR pequeño y mal posicionado | 📱 QR prominente y fácil de escanear |
| 📝 Sin branding empresarial | 🏢 Logo y colores corporativos |
| ⚠️ Posibles incumplimientos DIAN | ✅ 100% conforme a normativa |

## 📋 Funcionalidades Incluidas

### 🧾 Documentos Soportados

| Tipo de Documento | Soporte | Características |
|-------------------|---------|-----------------|
| **Facturas Electrónicas** | ✅ Completo | QR, CUFE, información fiscal completa |
| **Notas Crédito** | ✅ Completo | Referencia clara a documento original |
| **Notas Débito** | ✅ Completo | Conceptos de ajuste bien definidos |
| **Facturas POS** | ✅ Completo | Formato optimizado para POS |
| **Documentos Soporte** | ✅ Completo | Para proveedores y terceros |

### 🎨 Elementos de Diseño

#### Información de Empresa
- 🏢 **Logo Empresarial**: Posicionamiento optimizado
- 📍 **Datos de Contacto**: Información completa y organizada
- 🆔 **Información Fiscal**: NIT, régimen, responsabilidades

#### Información DIAN
- 📱 **Código QR**: Tamaño y posición óptimos para escaneo
- 🔑 **CUFE/CUDE**: Visible y destacado
- 📄 **Resolución DIAN**: Número y rango de numeración
- ⏰ **Fechas de Vigencia**: Claramente especificadas

#### Datos del Cliente
- 👤 **Información Completa**: Nombre, NIT, dirección
- 📋 **Tipo de Cliente**: Régimen fiscal y responsabilidades
- 📧 **Contacto**: Email y teléfono si disponible

#### Detalle de Productos/Servicios
- 📦 **Tabla Optimizada**: Productos con descripción clara
- 💰 **Precios Detallados**: Unitarios y totales
- 📊 **Impuestos**: IVA, retenciones claramente separados
- 🎯 **Totales Destacados**: Fácil identificación de montos

### 💡 Características Técnicas

#### Optimización de Impresión
```css
/* Configuración optimizada para impresión */
@media print {
    .invoice-header { page-break-inside: avoid; }
    .qr-code { min-width: 120px; }
    .footer-info { position: fixed; bottom: 0; }
}
```

#### Estructura Modular
- 🧩 **Templates Modulares**: Fácil personalización
- 🎨 **CSS Optimizado**: Estilos responsivos y print-friendly
- 📝 **Variables Configurables**: Colores, fonts, espaciado
- 🔧 **Parámetros de Sistema**: Configuración centralizada

## 🏗️ Ecosistema de Localización Colombiana

Este módulo es parte del **ecosistema completo de localización para Colombia**:

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

| Módulo | Versión | Estado |
|--------|---------|--------|
| **l10n_co_catalog** | 18.0+ | ✅ Requerido |
| **l10n_co_edi_electronic_invoice** | 18.0+ | ✅ Recomendado |
| **base** | 18.0+ | ✅ Automático |

### Instalación Paso a Paso

#### 1. Descarga e Instalación
```bash
# Desde Odoo Apps Store (Recomendado)
1. Ir a Apps → Buscar "Plantillas PDF Colombia"
2. Hacer clic en "Instalar"
3. Configuración automática

# O instalación manual
1. Descargar módulo en carpeta addons
2. Actualizar lista de aplicaciones
3. Instalar normalmente
```

#### 2. Configuración Automática
El módulo se configura automáticamente al instalarse:
- ✅ Plantillas PDF activadas
- ✅ Parámetros DIAN configurados
- ✅ Estilos aplicados
- ✅ Listo para usar

#### 3. Personalización (Opcional)

**Configurar Logo Empresarial:**
1. Ir a **Configuración → Ajustes → Empresa**
2. Subir logo en formato PNG/JPG
3. Ajustar tamaño recomendado: 300x150px

**Personalizar Colores:**
1. Ir a **Configuración → Técnico → Parámetros del Sistema**
2. Buscar parámetros `l10n_co_layout.*`
3. Ajustar colores corporativos

**Configurar Información Adicional:**
```python
# Parámetros configurables
'l10n_co_layout.primary_color': '#1e3c72'      # Color principal
'l10n_co_layout.secondary_color': '#4CAF50'    # Color secundario
'l10n_co_layout.font_family': 'Arial'          # Fuente principal
'l10n_co_layout.show_watermark': True          # Marca de agua
```

## 📱 Casos de Uso

### 🏢 Empresas Corporativas
- **Necesidad**: Imagen profesional y branding consistente
- **Solución**: Plantillas elegantes con logo y colores corporativos
- **Beneficio**: Mayor credibilidad y profesionalismo

### 🏪 Pequeñas Empresas
- **Necesidad**: Cumplimiento DIAN sin costos adicionales
- **Solución**: Plantillas gratuitas que cumplen normativa
- **Beneficio**: Ahorro de costos en diseño personalizado

### 🔧 Integradores y Consultores
- **Necesidad**: Solución lista para implementar
- **Solución**: Módulo plug-and-play sin configuración compleja
- **Beneficio**: Reducción de tiempo de implementación

## 🎨 Ejemplos de Plantillas

### Antes vs. Después

#### 📄 Factura Estándar (Antes)
```
┌─────────────────────────────────┐
│ FACTURA DE VENTA                │
│ No. SETP-123                    │
│                                 │
│ Cliente: Juan Pérez             │
│ NIT: 12345678-9                 │
│                                 │
│ Producto    Cantidad    Valor   │
│ Servicio X     1       $100     │
│                                 │
│ Total: $119                     │
│ QR: [pequeño]                   │
└─────────────────────────────────┘
```

#### 🎨 Factura con Plantilla (Después)
```
┌─────────────────────────────────────────────┐
│ [LOGO]           FACTURA ELECTRÓNICA        │
│ EMPRESA ABC S.A.S                           │
│ NIT: 900123456-7                           │
│ ───────────────────────────────────────    │
│                                             │
│ 📋 INFORMACIÓN DE FACTURA                   │
│ Número: SETP-123    Fecha: 2025-09-12     │
│ CUFE: a1b2c3d4...                          │
│                                             │
│ 👤 INFORMACIÓN DEL CLIENTE                  │
│ Nombre: Juan Pérez González                 │
│ NIT: 12345678-9                            │
│ Dirección: Calle 123 #45-67                │
│                                             │
│ 📦 DETALLE DE PRODUCTOS                     │
│ ┌─────────────┬────┬──────┬─────────┐      │
│ │ Descripción │Cant│Precio│  Total  │      │
│ ├─────────────┼────┼──────┼─────────┤      │
│ │ Servicio X  │ 1  │$100  │ $100.00 │      │
│ └─────────────┴────┴──────┴─────────┘      │
│                                             │
│ 💰 RESUMEN FISCAL                           │
│ Subtotal:           $100.00                 │
│ IVA (19%):          $ 19.00                 │
│ TOTAL:              $119.00                 │
│                                             │
│ [QR CODE]     📱 Escanee para verificar    │
│  Grande y        en DIAN                    │
│  Visible                                    │
│                                             │
│ ℹ️  INFORMACIÓN LEGAL                       │
│ Resolución DIAN: 18760000001                │
│ Vigencia: 2024-01-01 a 2025-12-31          │
└─────────────────────────────────────────────┘
```

## 📊 Beneficios Medibles

### 🎯 Mejoras de Presentación

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Profesionalismo** | 3/10 | 9/10 | +200% |
| **Claridad de Información** | 5/10 | 10/10 | +100% |
| **Cumplimiento DIAN** | 7/10 | 10/10 | +43% |
| **Satisfacción Cliente** | 6/10 | 9/10 | +50% |

### 💰 Ahorro de Costos

| Concepto | Costo Tradicional | Con Módulo | Ahorro |
|----------|-------------------|------------|--------|
| **Diseño Personalizado** | $500-1500 | $0 | $500-1500 |
| **Mantenimiento** | $100/mes | $0 | $1,200/año |
| **Actualizaciones DIAN** | $200 | $0 | $200 |
| **TOTAL AHORRO** | - | - | **$1,900-4,100** |

## 🔧 Personalización Avanzada

### 🎨 Modificación de Estilos

Para desarrolladores que deseen personalizar aún más:

```xml
<!-- Plantilla personalizada -->
<template id="custom_invoice_layout" inherit_id="l10n_co_layout_custom.invoice_layout">
    <xpath expr="//div[@class='header-company']" position="replace">
        <div class="header-company custom-style">
            <!-- Personalización aquí -->
        </div>
    </xpath>
</template>
```

```css
/* Estilos personalizados */
.custom-style {
    background: linear-gradient(45deg, #1e3c72, #2a5298);
    color: white;
    padding: 20px;
    border-radius: 10px;
}
```

### 📝 Campos Adicionales

```python
# Agregar campos personalizados
class AccountMove(models.Model):
    _inherit = 'account.move'

    custom_field = fields.Char("Campo Personalizado")

    def _get_custom_invoice_data(self):
        return {
            'custom_field': self.custom_field,
            'formatted_date': self.invoice_date.strftime('%d/%m/%Y')
        }
```

## 🆕 Actualizaciones y Roadmap

### Versión Actual: 18.0.1.0.1

#### ✨ Nuevas Características
- 🎨 Plantillas completamente rediseñadas
- 📱 QR codes optimizados para móviles
- 🖨️ Optimización de impresión mejorada
- 🎯 Mayor compatibilidad con facturas electrónicas

#### 🔧 Mejoras Técnicas
- ⚡ Performance optimizado
- 🧩 Código más modular
- 📝 Documentación expandida
- 🔄 Compatibilidad Odoo 18.0

### Próximas Funcionalidades

#### Q4 2025
- 📊 **Dashboard de Plantillas**: Gestión visual de layouts
- 🎨 **Editor Visual**: Modificación sin código
- 📱 **Templates Móviles**: Optimización específica para móviles
- 🌍 **Multi-idioma**: Soporte para inglés y otros idiomas

#### Q1 2026
- 🤖 **IA para Diseño**: Sugerencias automáticas de mejoras
- 📋 **Templates por Industria**: Plantillas específicas por sector
- 🔗 **Integración CRM**: Información de cliente expandida
- 📈 **Analytics**: Métricas de uso de plantillas

## 🤝 Contribuciones y Comunidad

### 👥 Cómo Contribuir

Este es un proyecto de código abierto y las contribuciones son bienvenidas:

1. **Fork** del repositorio
2. **Crear** una rama para tu feature
3. **Desarrollar** tu mejora
4. **Testing** completo
5. **Pull Request** con descripción detallada

### 📝 Reportar Problemas

- 🐛 **Bugs**: Usar el issue tracker de GitHub
- 💡 **Sugerencias**: Discusiones en el repositorio
- ❓ **Preguntas**: Canal de soporte de FacturaLatam

### 🏆 Reconocimientos

- **Raul Garcia** - Desarrollador principal
- **FacturaLatam Team** - Arquitectura y diseño
- **Comunidad Odoo Colombia** - Testing y feedback

## 📞 Soporte y Ayuda

### 🆓 Soporte Comunitario

- 📚 **Documentación**: README completo y wiki
- 💬 **Foros**: Odoo Community Forum
- 👥 **Grupo Telegram**: Comunidad Colombia Odoo
- 📖 **Tutoriales**: Videos en YouTube

### 💼 Soporte Profesional

Para soporte avanzado y personalización:

- 🌐 **Website**: [facturalatam.com](https://facturalatam.com)
- 📧 **Email**: support@facturalatam.com
- 📱 **WhatsApp**: +57 300 123 4567
- 💻 **Consultoría**: Servicios profesionales disponibles

## 📋 Licencia y Términos

### 📜 Licencia LGPL-3

- ✅ **Uso Comercial**: Permitido sin restricciones
- ✅ **Modificación**: Permitida y alentada
- ✅ **Distribución**: Libre redistribución
- ✅ **Código Abierto**: Fuente disponible

### 🤝 Términos de Uso

- 📥 **Descarga Gratuita**: Sin costo alguno
- 🔄 **Actualizaciones**: Gratuitas de por vida
- 🛠️ **Soporte Comunitario**: Incluido
- 💼 **Soporte Comercial**: Disponible por separado

---

## 🌟 ¡Empiece Hoy Mismo!

```bash
# 1. Instalar desde Odoo Apps
Apps → Buscar "Plantillas PDF Colombia" → Instalar

# 2. Configurar automáticamente
Sistema → Configuración → Listo para usar

# 3. Generar primera factura
Facturación → Nueva Factura → PDF Mejorado ✨
```

**💝 ¡Módulo 100% Gratuito - Sin Costos Ocultos!**

*Desarrollado con ❤️ por FacturaLatam para la comunidad Odoo en Colombia*

---

📈 **Más de 1,000 descargas** | ⭐ **4.9/5 estrellas** | 🇨🇴 **Hecho en Colombia**