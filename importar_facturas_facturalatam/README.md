# Importar Facturas Facturalatam

Módulo para Odoo que extiende la funcionalidad de compras permitiendo importar archivos XML de facturas electrónicas colombianas y crear automáticamente proveedores y productos.

## Características

- **Importación de XML**: Permite cargar archivos XML de facturas electrónicas directamente en las órdenes de compra
- **Creación automática de proveedores**: Extrae información del proveedor del XML y crea registros automáticamente si no existen
- **Creación automática de productos**: Procesa las líneas de factura y crea productos con sus especificaciones
- **Mapeo de unidades de medida**: Utiliza el catálogo DIAN para mapear correctamente las unidades de medida
- **Integración con localización colombiana**: Compatible con el módulo `l10n_co_catalog` para unidades de medida DIAN
- **Transferencia de CUFE a facturas**: Cuando se crea una factura desde la orden de compra, el CUFE se transfiere automáticamente al campo `ei_uuid`

## 🏗️ Ecosistema de Localización Colombiana

Este módulo forma parte del **ecosistema completo de localización para Colombia**:

```
🇨🇴 Localización Colombia - Ecosistema Completo
├── 🆓 l10n_co_catalog                    # MÓDULO BASE (GRATUITO)
│   └── ⚡ Requerido para este módulo
├── 💰 l10n_co_edi_electronic_invoice     # MÓDULO COMERCIAL ($299 USD)
│   └── ⚡ Se potencia con este módulo
├── 🆓 l10n_co_layout_custom              # COMPLEMENTO (GRATUITO)
│   └── ⚡ Compatible con este módulo
└── 🆓 importar_facturas_facturalatam     # ESTE MÓDULO (GRATUITO)
    ├── 🎯 Utilidad de importación XML
    └── 🔄 Automatización de procesos
```

## Dependencias

- `base`: Módulo base de Odoo
- `purchase`: Módulo de compras de Odoo
- `l10n_co_catalog`: Catálogo colombiano para unidades de medida DIAN

## Instalación

1. Copiar el módulo en la carpeta de addons
2. Actualizar la lista de módulos
3. Instalar el módulo `importar_facturas_facturalatam`

## Uso

1. Ir a **Compras > Órdenes de compra**
2. Crear una nueva orden de compra o abrir una existente en estado borrador
3. Hacer clic en el botón **"Importar Factura"**
4. Seleccionar el archivo XML o ZIP de la factura electrónica
5. Hacer clic en **"Importar"**

El sistema automáticamente:
- Creará o actualizará el proveedor con los datos del XML
- Establecerá la referencia del proveedor con el número de factura y CUFE
- Guardará el CUFE del XML para transferirlo a facturas futuras
- Creará las líneas de productos con precios y cantidades
- Creará productos nuevos si no existen en el sistema

## Transferencia de CUFE a Facturas

Cuando se crea una factura a partir de una orden de compra que fue importada desde XML:

1. **El CUFE se transfiere automáticamente** al campo `ei_uuid` de la factura
2. **Se registra en los logs** para seguimiento
3. **Funciona tanto con facturas creadas manualmente** como con el proceso automático
4. **Solo se transfiere si el campo `ei_uuid` existe** (compatible con módulos de facturación electrónica)

## Estructura del XML soportada

El módulo procesa los siguientes elementos del XML de factura electrónica:

### Información del proveedor
```xml
<cac:AccountingSupplierParty>
    <cac:Party>
        <cac:PartyName>
            <cbc:Name>Nombre del proveedor</cbc:Name>
        </cac:PartyName>
        <cac:PhysicalLocation>
            <cac:Address>
                <cbc:ID>codigo del municipio</cbc:ID>
                <cbc:CityName>Nombre del municipio</cbc:CityName>
                <cbc:CountrySubentity>Nombre del estado</cbc:CountrySubentity>
                <cbc:CountrySubentityCode>codigo del estado</cbc:CountrySubentityCode>
                <cac:AddressLine>
                    <cbc:Line>Direccion</cbc:Line>
                </cac:AddressLine>
                <cac:Country>
                    <cbc:IdentificationCode>Codigo del pais</cbc:IdentificationCode>
                    <cbc:Name languageID="es">nombre del pais</cbc:Name>
                </cac:Country>
            </cac:Address>
        </cac:PhysicalLocation>
        <cac:Contact>
            <cbc:Telephone>telefono del proveedor</cbc:Telephone>
            <cbc:ElectronicMail>correo electronico del proveedor</cbc:ElectronicMail>
        </cac:Contact>
    </cac:Party>
</cac:AccountingSupplierParty>
```

### Información de la factura
```xml
<cbc:ID>numero de la factura</cbc:ID>
<cbc:UUID schemeID="1" schemeName="CUFE-SHA384">numero del CUFE</cbc:UUID>
```

### Líneas de productos
```xml
<cac:InvoiceLine>
    <cbc:ID>numero de la linea</cbc:ID>
    <cbc:Description>nombre del producto</cbc:Description>
    <cbc:BrandName>marca</cbc:BrandName>
    <cbc:ModelName>modelo</cbc:ModelName>
    <cac:Item>
        <cac:StandardItemIdentification>
            <cbc:ID schemeID="999" schemeName="Estándar de adopción del contribuyente">referencia interna</cbc:ID>
        </cac:StandardItemIdentification>
    </cac:Item>
    <cac:Price>
        <cbc:PriceAmount currencyID="COP">valor unitario</cbc:PriceAmount>
        <cbc:BaseQuantity unitCode="NIU">cantidad</cbc:BaseQuantity>
    </cac:Price>
</cac:InvoiceLine>
```

## Mapeo de unidades de medida

El módulo utiliza el catálogo DIAN (`l10n_co_fl.unit.measure`) para mapear correctamente las unidades de medida del XML a las unidades de medida de Odoo através del campo `edi_unit_measure_id`.

Como fallback, incluye un mapeo común para los códigos más utilizados:
- NIU: Unidades
- KGM: Kilogramos
- LTR: Litros
- MTR: Metros
- MTK: Metros cuadrados
- MTQ: Metros cúbicos
- HUR: Horas
- DAY: Días
- TNE: Toneladas
- GRM: Gramos

## Autor

Desarrollado para Odoo 18.0

## Licencia

LGPL-3
