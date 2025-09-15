{
    "name": "Plantillas PDF Colombia - Representación Impresa DIAN",
    "version": "18.0.1.0.1",
    "category": "Reporting",
    "summary": "Plantillas PDF personalizadas para Colombia con representación impresa oficial DIAN",
    "description": """
        Módulo complementario para personalizar las plantillas PDF de facturas electrónicas en Colombia.

        Características principales:
        • Plantillas PDF profesionales adaptadas a normativa DIAN
        • Representación impresa oficial según resolución 000042 de 2020
        • Diseño optimizado para facturas, notas crédito y débito
        • Información fiscal completa y organizada
        • QR code y CUFE visibles y bien posicionados
        • Logos y branding empresarial personalizable
        • Compatible con facturas electrónicas y documentos EDI

        Complementa perfectamente los módulos de facturación electrónica.
        Mejora la presentación profesional de documentos fiscales.
    """,
    "author": "FacturaLatam",
    "website": "https://facturalatam.com",
    "support": "soporte@facturalatam.com",
    "contributors": ["Raul Garcia"],
    "license": "LGPL-3",
    "depends": [
        "l10n_co_catalog",
        "l10n_co_edi_electronic_invoice",
    ],
    "data": [
        "data/config_parameter.xml",
        "templates/report_templates.xml",
        "data/report_layout.xml",
        "templates/report_invoice.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    'images': [
        'static/description/banner.png',
    ],
    'price': 0.0,
    'currency': 'USD',
}
