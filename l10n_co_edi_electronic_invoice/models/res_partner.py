# -*- coding: utf-8 -*-


import logging
import re

from odoo import fields, models, api
import requests
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"


    l10n_co_edi_type_document_identification_id = fields.Many2one('l10n_co_fl.type_document_identification',default= 3 ,string="Tipo de Identificación")
    identification_co_number = fields.Char(string='Número de Identificación')
    municipality_id = fields.Many2one('l10n_co_fl.municipality', string="Municipio")
    l10n_co_edi_merchant_registration = fields.Char(string="Registro Mercantil")
    l10n_co_edi_type_organization_id = fields.Many2one('l10n_co_fl.type.organization', string="Tipo de Organización", default=lambda self: self.env['l10n_co_fl.type.organization'].search([], limit=1))
    l10n_co_edi_type_liability_id = fields.Many2one('l10n_co_fl.type.liability', string="Tipo de Responsabilidad", default=lambda self: self.env['l10n_co_fl.type.liability'].search([], limit=1))
    type_regime_id  = fields.Many2one('l10n_co_fl.type.regime', string="Tipo de Régimen", default=lambda self: self.env['l10n_co_fl.type.regime'].search([], limit=1))

    def action_consultar_identificacion(self):
        for partner in self:
            type_identification = partner.l10n_co_edi_type_document_identification_id.code
            number = partner.identification_co_number
            if not type_identification or not number:
                raise UserError("Debe ingresar el tipo y número de identificación.")

            company = self.env.company
            while company.parent_id:
                company = company.parent_id
            headers = company.get_header_bearer()
            get_endpoint = company.get_endpoint('SearchCustomer')
            base_url = company.format_url(company.ip_domain, get_endpoint)
            url = f"{base_url}/{type_identification}/{number}"

            try:
                response = requests.get(url, headers=headers, timeout=company.api_timeout, verify=False)
                response.raise_for_status()
                result = response.json()

                _logger.info("SearchCustomer url: %s", url)
                _logger.info("SearchCustomer respose: %s", result)

                get_acquirer_result = (
                    result.get('ResponseDian', {})
                    .get('GetAcquirerResponse', {})
                    .get('GetAcquirerResult', {})
                )
                receiver_name = get_acquirer_result.get('ReceiverName')
                receiver_email = get_acquirer_result.get('ReceiverEmail')

                vals = {}
                if receiver_name:
                    vals['name'] = receiver_name
                if receiver_email:
                    vals['email'] = receiver_email

                if vals:
                    partner.write(vals)
                    partner.message_post(body=f"Datos autocompletados: {vals}")
                else:
                    partner.message_post(body=f"Consulta realizada, pero no se encontraron datos para autocompletar.<br/>Respuesta: {result}")

            except Exception as e:
                raise UserError(f"Error al consultar la identificación: {e}")
