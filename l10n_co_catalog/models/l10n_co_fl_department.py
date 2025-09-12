from odoo import models, fields

class L10nCoFlDepartment(models.Model):
    _name = 'l10n_co_fl.department'
    _description = 'Department'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
