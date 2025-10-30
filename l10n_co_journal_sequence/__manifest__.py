# -*- coding: utf-8 -*-
{
    'name': 'Secuencias de Diario',
    'version': '18.0.1.0.0',
    'author': 'FacturaLatam',
    'website': 'https://facturalatam.com',
    'support': 'soporte@facturalatam.com',
    'category': 'Accounting/Localizations',
    'description': """
Secuencias de Diario Colombiano
==============================

Este módulo proporciona una gestión simplificada de secuencias para entradas de diario
en la localización de Colombia. Crea campos de secuencia en diarios contables con
configuración mínima requerida.

Características:
- Campos de secuencia estándar para entradas y notas de crédito
- Gestión automática del número siguiente
- Integración directa con diarios contables
- Configuración simplificada para necesidades básicas de numeración

Este es un módulo liviano para numeración básica en diarios colombianos.
    """,
    'summary': 'Gestión simplificada de secuencias para diarios colombianos',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_journal_views.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'predecessor': 'journal_sequence',
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'USD',
}
