from odoo import models, fields

class L10nCoFlCreditNoteDiscrepancy(models.Model):
    _name = 'l10n_co_fl.credit_note.discrepancy'
    _description = 'Credit Note Discrepancy'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
