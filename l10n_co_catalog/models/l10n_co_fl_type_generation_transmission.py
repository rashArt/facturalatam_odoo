from odoo import models, fields

class L10nCoFlTypeGenerationTransmission(models.Model):
    _name = 'l10n_co_fl.type.generation.transmission'
    _description = 'Type Generation Transmission'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
