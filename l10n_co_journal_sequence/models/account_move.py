# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    sequence_generated = fields.Boolean(
        string="Secuencia Generada",
        copy=False,
        help="Indica si el número de secuencia ha sido generado"
    )

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        """
        Sobrescribir el cálculo de nombre para usar secuencias de diario cuando estén disponibles.
        """
        for move in self:
            if not move.journal_id.sequence_id:
                return super(AccountMove, self)._compute_name()
            sequence_id = move._get_sequence()
            if not sequence_id:
                raise UserError('Por favor defina una secuencia en su diario.')
            # if not move.sequence_generated and move.state == 'draft':
            #     move.name = '/'
            elif not move.sequence_generated and move.state != 'draft':
                date = False
                if move.invoice_date:
                    date = move.invoice_date
                elif move.date:
                    date = move.date
                move.name = sequence_id.with_context({'ir_sequence_date': date, 'bypass_constrains': True}).next_by_id(sequence_date=date)
                move.sequence_generated = True

    def _get_sequence(self):
        '''Devolver la secuencia a utilizar durante el post del movimiento actual.
        :return: Un registro ir.sequence o False.
        '''
        self.ensure_one()

        journal = self.journal_id
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
        if not journal.refund_sequence_id:
            return
        return journal.refund_sequence_id
