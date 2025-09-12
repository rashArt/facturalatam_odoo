from odoo import models, fields

class L10nCoFlTypeItemIdentification(models.Model):
    _name = 'l10n_co_fl.type.item.identification'
    _description = 'Type Item Identification'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    code_agency = fields.Char(string='Code Agency')
