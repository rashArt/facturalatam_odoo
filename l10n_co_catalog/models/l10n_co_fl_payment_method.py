from odoo import models, fields

class L10nCoFlPaymentMethod(models.Model):
    _name = 'l10n_co_fl.payment.method'
    _description = 'Payment Method'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
