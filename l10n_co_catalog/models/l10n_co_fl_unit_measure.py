from odoo import models, fields

class L10nCoFlUnitMeasure(models.Model):
    _name = 'l10n_co_fl.unit.measure'
    _description = 'Unit Measure'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
