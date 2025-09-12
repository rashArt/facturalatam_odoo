from odoo import models, fields

class L10nCoFlTax(models.Model):
    _name = 'l10n_co_fl.tax'
    _description = 'Tax'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Char(string='Description')
