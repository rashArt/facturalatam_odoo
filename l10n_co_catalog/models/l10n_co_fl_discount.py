from odoo import models, fields

class L10nCoFlDiscount(models.Model):
    _name = 'l10n_co_fl.discount'
    _description = 'Discount'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
