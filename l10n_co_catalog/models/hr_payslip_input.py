from odoo import models, fields, api

class HrPayslipInput(models.Model):
    _inherit = "hr.payslip.input"

    rule_id = fields.Many2one(
        'hr.salary.rule',
        string="Salary Rule",
        help="Select a salary rule. The code will be automatically assigned."
    )

    @api.onchange('rule_id')
    def _onchange_rule_id(self):
        """Cuando se seleccione una regla, llenar automáticamente el campo code."""
        if self.rule_id:
            self.code = self.rule_id.code