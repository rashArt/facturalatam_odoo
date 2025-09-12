from odoo import models, fields

class L10nCoFlCountry(models.Model):
    _name = 'l10n_co_fl.country'
    _description = 'Country'

    id = fields.Char(string='ID', required=True)
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
