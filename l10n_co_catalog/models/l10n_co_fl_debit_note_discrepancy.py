from odoo import models, fields

class L10nCoFlDebitNoteDiscrepancy(models.Model):
    _name = 'l10n_co_fl.debit_note.discrepancy'
    _description = 'Debit Note Discrepancy'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
