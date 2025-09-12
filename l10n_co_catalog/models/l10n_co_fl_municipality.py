from odoo import models, fields, api

class L10nCoFlMunicipality(models.Model):
    _name = 'l10n_co_fl.municipality'
    _description = 'Municipality'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    department_id = fields.Many2one('l10n_co_fl.department', string='Department', required=True)
    codefacturador = fields.Integer(string='Codefacturador')

    @api.depends('name', 'department_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.department_id and record.department_id.name:
                department_initials = ''.join(word[:3].upper() for word in record.department_id.name.split())
                record.display_name = f"{record.name} ({department_initials})"
            else:
                record.display_name = record.name
