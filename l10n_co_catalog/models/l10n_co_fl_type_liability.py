from odoo import models, fields

class L10nCoFlTypeLiability(models.Model):
    _name = 'l10n_co_fl.type.liability'
    _description = 'Type Liability'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
