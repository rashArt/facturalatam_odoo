from odoo import models, fields

class L10nCoFlTypeDocument(models.Model):
    _name = 'l10n_co_fl.type_document'
    _description = 'Type Documents'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', )
    cufe_algorithm = fields.Char(string='CUFE Algorithm')
    prefix = fields.Char(string='CUFE Prefix')
