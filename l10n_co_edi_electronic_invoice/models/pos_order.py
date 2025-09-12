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
            journal = invoice.journal_id
            company = invoice.company_id
            partner = invoice.partner_id
            return {
                "is_electronic_invoice": invoice.is_electronic_invoice,
                "ei_is_valid": invoice.ei_is_valid,
                "ei_status": invoice.ei_status,
                "ei_uuid": invoice.ei_uuid,
                "ei_qr_image": invoice.ei_qr_image,
                "ei_number": invoice.name,
                "journal": {
                    "prefix": journal.prefix,
                    "resolution": journal.resolution,
                    "resolution_date": journal.resolution_date,
                    "from_number": journal.from_number,
                    "to_number": journal.to_number,
                    "date_from": journal.date_from,
                    "date_to": journal.date_to,
                    "technical_key": journal.technical_key
                },
                "company": {
                    "name": company.business_name,
                    "identification_number": company.identification_number,
                    "address": company.address,
                    "type_document_identification_id": company.type_document_identification_id.name,
                },
                "partner": {
                    "name": partner.name if partner else "",
                    "identification_co_number": partner.identification_co_number if partner else "",
                    "l10n_co_edi_type_document_identification_id": partner.l10n_co_edi_type_document_identification_id.name if partner else "",
                }
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

