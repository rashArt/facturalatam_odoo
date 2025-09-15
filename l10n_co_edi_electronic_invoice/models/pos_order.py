# -*- coding: utf-8 -*-
#
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def get_account_move(self):
        invoice = self.account_move
        if invoice.is_electronic_invoice:
            invoice.send_electronic_invoice()
            return {
                "is_electronic_invoice": invoice.is_electronic_invoice,
                "ei_is_valid": invoice.ei_is_valid,
                "ei_status": invoice.ei_status,
                "ei_uuid": invoice.ei_uuid,
                "ei_qr_image": invoice.ei_qr_image,
                "ei_number": invoice.name,
            }
        return None

    def _prepare_invoice_vals(self):
        self.ensure_one()

        # Llamar al método original para obtener los valores por defecto
        vals = super(PosOrder, self)._prepare_invoice_vals()

        # Condición para cambiar el diario si es un reembolso
        if self.lines.filtered(lambda line: line.refunded_orderline_id):
            refund_journal = self.env['account.journal'].search([
                ('type', '=', 'sale'),  # Tipo de diario "Venta"
                ('is_electronic_invoice', '=', True),  # Diario electrónico
                ('resolution_type_document_id', '=', 4)  # Relacionado con el ID 4
            ], limit=1)
            if refund_journal:
                vals['journal_id'] = refund_journal.id
                vals['ei_correction_concept_credit_id'] = 2  # ID del concepto de corrección para reembolsos
        return vals

