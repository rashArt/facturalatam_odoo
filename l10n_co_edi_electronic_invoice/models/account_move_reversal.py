# -*- coding: utf-8 -*-


from odoo import models, fields, api


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'


    ei_correction_concept_credit_id = fields.Many2one('l10n_co_fl.credit_note.discrepancy', string='Motivo Credito', copy=False)
    journal_document_id = fields.Integer(
        string="Tipo de Documento del Diario",
        store=False
    )

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        if self.journal_id and self.journal_id.resolution_type_document_id:
            self.journal_document_id = self.journal_id.resolution_type_document_id.id
        else:
            self.journal_document_id = False

    @api.onchange('ei_correction_concept_credit_id')
    def _onchange_ei_correction_concept_credit_id(self):
        if self.ei_correction_concept_credit_id:
            self.reason = self.ei_correction_concept_credit_id.name

    def _prepare_default_reversal(self, move):
        values = super(AccountMoveReversal, self)._prepare_default_reversal(move)

        if self.ei_correction_concept_credit_id:
            values['ei_correction_concept_credit_id'] = self.ei_correction_concept_credit_id.id

        return values


    @api.depends("move_ids")
    def _compute_available_journal_ids(self):
        res = super(AccountMoveReversal, self)._compute_available_journal_ids()
        for rec in self:
            move_ids = self.env["account.move"].browse(rec.move_ids.ids)
            if all(move.is_electronic_invoice for move in move_ids):
                rec.available_journal_ids = self.env["account.journal"].search(
                    [("resolution_type_document_id.code", "in", ["91", "95", "2"])]
                )
        return res

    @api.depends("move_ids", "available_journal_ids")
    def _compute_journal_id(self):
        res = super(AccountMoveReversal, self)._compute_journal_id()
        for rec in self:
            move_ids = self.env["account.move"].browse(rec.move_ids.ids)
            if all(move.is_electronic_invoice for move in move_ids):
                rec.journal_id = (
                    rec.available_journal_ids
                    and rec.available_journal_ids[0]._origin
                    or False
                )
        return res