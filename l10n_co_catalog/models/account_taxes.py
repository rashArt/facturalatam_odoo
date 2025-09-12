# -*- coding: utf-8 -*-


from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    edi_tax_id = fields.Many2one('l10n_co_fl.tax', string="Tipo de impuesto (DIAN)", ondelete='RESTRICT', copy=True)

    dian_report_tax_base = fields.Selection([
        ('auto', 'automático'),
        ('no_report', 'No reportar la base imponible a la DIAN')
    ], string="base imponible (DIAN)", default='auto', copy=True)
