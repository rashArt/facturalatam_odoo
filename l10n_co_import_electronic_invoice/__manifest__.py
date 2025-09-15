{
    'name': 'Importar Facturas Electrónicas Colombia',
    'version': '18.0.1.0.1',
    'author': 'Ricardo Colonia',
    'website': 'https://rcstudio.dev',
    'support': 'support@rcstudio.dev',
    'category': 'Purchases',
    'summary': 'Importar XML de facturas electrónicas colombianas y crear automáticamente proveedores, productos y órdenes de compra',
    'description': """
Importar Facturas Electrónicas Colombia
=======================================
Módulo que permite importar archivos XML de facturas electrónicas colombianas para crear automáticamente:

• Proveedores con información completa del XML
• Productos con especificaciones detalladas
• Órdenes de compra con líneas de pedido automáticas
• Transferencia de CUFE a facturas de proveedor
• Mapeo automático de unidades de medida DIAN

Características principales:
- Compatible con formato XML de facturas electrónicas DIAN
- Creación automática de registros de proveedores
- Mapeo inteligente de unidades de medida colombianas
- Transferencia automática de CUFE a facturas
- Integración completa con módulo de compras de Odoo

Simplifica el proceso de registro de facturas de proveedores colombianos.
    """,
    'depends': ['base', 'purchase', 'account', 'l10n_co_catalog'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'wizard/xml_import_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.png',
    ],
    'price': 0.0,
    'currency': 'USD',
}