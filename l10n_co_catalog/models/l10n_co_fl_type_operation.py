from odoo import models, fields

class L10nCoFlTypeOperation(models.Model):
    _name = 'l10n_co_fl.type_operation'
    _description = 'Type Operation'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
