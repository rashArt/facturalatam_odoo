# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'
    
    ei_correction_concept_debit_id = fields.Many2one('l10n_co_fl.debit_note.discrepancy', string='Motivo Débito', copy=False)
    available_journal_ids = fields.Many2many(
        comodel_name="account.journal", compute="_compute_available_journal_ids"
    )
    journal_id = fields.Many2one(
        compute="_compute_journal_id", required=True, readonly=False, store=True
    )
    
    @api.depends("move_ids")
    def _compute_available_journal_ids(self):

        for rec in self:
            move_ids = self.env["account.move"].browse(rec.move_ids.ids)
            if all(move.is_electronic_invoice for move in move_ids):
                rec.available_journal_ids = self.env["account.journal"].search(
                    [("resolution_type_document_id.code", "=", "92")]
                )
     
    
    @api.depends("move_ids", "available_journal_ids")
    def _compute_journal_id(self):
        for rec in self:
            move_ids = self.env["account.move"].browse(rec.move_ids.ids)
            if all(move.is_electronic_invoice for move in move_ids):
                rec.journal_id = (
                    rec.available_journal_ids
                    and rec.available_journal_ids[0]._origin
                    or False
                )
      
    
    
    def _prepare_default_values(self, move):
        res = super(AccountDebitNote, self)._prepare_default_values(move)
        res.update(
            {
                "ei_correction_concept_debit_id": self.ei_correction_concept_debit_id.id,
            }
        )
        return res