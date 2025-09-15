{
    'name': 'Facturación Electrónica Colombia - EDI DIAN',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Facturación Electrónica Colombia - Integración completa con DIAN',
    'description': """
        Módulo profesional para facturación electrónica en Colombia con integración completa a la DIAN.

        Características principales:
        • Generación automática de facturas electrónicas según normativa DIAN
        • Envío automático a API certificada para firma digital
        • Transmisión directa a la DIAN y obtención de CUFE
        • Soporte completo para facturas, notas crédito y débito
        • Integración con POS para facturación electrónica en tiempo real
        • Reportes y trazabilidad completa de documentos EDI
        • Configuración automática según resolución DIAN
        • Manejo de contingencias y documentos offline

        Cumple 100% con la resolución 000042 de 2020 de la DIAN.
        Incluye soporte técnico especializado.
    """,
    'author': 'FacturaLatam',
    'contributors': ['Enrique Huayas Macha', 'Raul Garcia'],
    'website': 'https://facturalatam.com',
    'support': 'soporte@facturalatam.com',
    'price': 500.00,
    'currency': 'USD',
    'depends': [
        'account',
        'l10n_co_catalog',
        'account_debit_note',
        'sale_management',
        'l10n_co_global_discount',
        'point_of_sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/co_request_edi_views.xml',
        'views/co_log_edi_views.xml',
        'views/res_partner_view.xml',
        'views/account_move_reversal_view.xml',
        'views/account_debit_note_views.xml',
        'reports/export_invoice_report.xml',
        'data/account_move_mass_action.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'l10n_co_edi_electronic_invoice/static/src/js/payment_screen.js',
            'l10n_co_edi_electronic_invoice/static/src/js/pos_store.js',
            'l10n_co_edi_electronic_invoice/static/src/js/partner_editor.js',
            'l10n_co_edi_electronic_invoice/static/src/xml/payment_screen.xml',
            'l10n_co_edi_electronic_invoice/static/src/xml/partner_editor.xml',
            'l10n_co_edi_electronic_invoice/static/src/xml/receipt_header.xml',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
