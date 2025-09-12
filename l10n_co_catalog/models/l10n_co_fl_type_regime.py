from odoo import models, fields

class L10nCoFlTypeRegime(models.Model):
    _name = 'l10n_co_fl.type.regime'
    _description = 'Type Regime'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
