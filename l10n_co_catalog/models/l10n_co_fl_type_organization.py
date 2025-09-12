from odoo import models, fields

class L10nCoFlTypeOrganization(models.Model):
    _name = 'l10n_co_fl.type.organization'
    _description = 'Type Organization'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
