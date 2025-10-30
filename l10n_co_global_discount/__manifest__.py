{
    'name': 'Descuentos Globales Colombia',
    'version': '17.0.1.0.3',
    'category': 'Localization',
    'summary': 'Descuentos globales para órdenes de venta y facturas - Localización Colombia',
    'description': """
        Módulo de descuentos globales adaptado para la localización colombiana.

        Características principales:
        • Descuentos globales en órdenes de venta
        • Descuentos globales en facturas
        • Cálculo automático de impuestos según normativa colombiana
        • Compatible con facturación electrónica DIAN
        • Integración perfecta con módulos de localización colombiana
        • Manejo de descuentos por porcentaje o valor fijo
        • Configuración centralizada de descuentos por defecto

        Forma parte del ecosistema completo de localización colombiana para Odoo 17.
        Mejora la gestión comercial con descuentos profesionales.
    """,
    'author': 'FacturaLatam',
    'website': 'https://facturalatam.com',
    'support': 'soporte@facturalatam.com',
    'contributors': ['Enrique Huayas Macha', 'Raul Garcia'],
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'account',
    ],
    'data': [
        'data/default_product_discount.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [
        'static/description/banner.png',
    ],
    'price': 0.0,
    'currency': 'USD',
}
