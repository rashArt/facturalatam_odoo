# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de Entradas',
        help="Este campo contiene la información relacionada con la numeración de las entradas del diario de este diario.",
        copy=False
    )
    refund_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de Notas de Crédito',
        help="Este campo contiene la información relacionada con la numeración de las notas de crédito de este diario.",
        copy=False
    )
    sequence_number_next = fields.Integer(
        string='Siguiente Número',
        help='El siguiente número de secuencia se utilizará para la próxima factura.',
        compute='_compute_sequence_number_next',
        inverse='_inverse_sequence_number_next'
    )
    refund_sequence_number_next = fields.Integer(
        string='Siguiente Número de Notas de Crédito',
        help='El siguiente número de secuencia se utilizará para la próxima nota de crédito.',
        compute='_compute_refund_sequence_number_next',
        inverse='_inverse_refund_sequence_number_next'
    )

    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_sequence_number_next(self):
        """Calcular 'sequence_number_next' según la secuencia actual en uso."""
        for journal in self:
            if journal.sequence_id:
                sequence = journal.sequence_id._get_current_sequence()
                journal.sequence_number_next = sequence.number_next_actual
            else:
                journal.sequence_number_next = 1

    def _inverse_sequence_number_next(self):
        """Invertir 'sequence_number_next' para editar el siguiente número de la secuencia actual."""
        for journal in self:
            if journal.sequence_id and journal.sequence_number_next:
                sequence = journal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.sequence_number_next

    @api.depends('refund_sequence_id.use_date_range', 'refund_sequence_id.number_next_actual')
    def _compute_refund_sequence_number_next(self):
        """Calcular 'refund_sequence_number_next' según la secuencia actual en uso."""
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence:
                sequence = journal.refund_sequence_id._get_current_sequence()
                journal.refund_sequence_number_next = sequence.number_next_actual
            else:
                journal.refund_sequence_number_next = 1

    def _inverse_refund_sequence_number_next(self):
        """Invertir 'refund_sequence_number_next' para editar el siguiente número de la secuencia actual."""
        for journal in self:
            if journal.refund_sequence_id and journal.refund_sequence and journal.refund_sequence_number_next:
                sequence = journal.refund_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.refund_sequence_number_next

