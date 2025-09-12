# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
import json
import requests
import logging


_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_electronic_invoice = fields.Boolean(string='¿Es un documento electrónico?', default=False)
    resolution_type_document_id = fields.Many2one(comodel_name="l10n_co_fl.type_document", string='Tipo de Comprobante', ondelete='RESTRICT')
    edi_establishment_id = fields.Many2one('l10n_co_edi.establishment', string="Establecimiento", ondelete='RESTRICT')
    prefix = fields.Char(string='Prefijo')
    resolution = fields.Char(string='Resolución')
    resolution_date = fields.Date(string='Fecha de Resolución')
    from_number = fields.Integer(string='Del número')
    to_number = fields.Integer(string='Al número')
    generate_to_date = fields.Date(string='Generar hasta la fecha')
    date_from = fields.Date(string='Desde la fecha')
    date_to = fields.Date(string='Hasta la fecha')
    technical_key = fields.Char(string='Clave Técnica')
    is_out_country = fields.Boolean(string='¿Es factura de exportación?', default=False)
    is_valid_resolution_config = fields.Boolean(string='Configuración de Resolución Válida', default=False)
    api_message_resolution = fields.Text(string='Mensaje de API de Resolución')

    def validate_resolution_data(self):
        if self.is_electronic_invoice:

            if  self.prefix not in self.sequence_id.prefix:
                raise UserError("El prefijo de la secuencia no coincide con el prefijo de la resolución.")
            if self.sequence_id.number_next_actual < self.from_number:
                raise UserError("El número siguiente de la secuencia debe ser mayor o igual al número inicial de la resolución.")
            if not self.sequence_id:
                raise UserError("Por favor asigne una secuencia al diario antes de continuar.")
            if self.from_number >= self.to_number:
                raise UserError("El número inicial debe ser menor que el número final.")

            required_fields = [
                ('resolution_type_document_id', 'tipo de documento'),
                ('prefix', 'prefijo'),
                ('from_number', 'número inicial'),
                ('to_number', 'número final'),
            ]

            if self.resolution_type_document_id.id == 1:
                if not self.technical_key:
                    raise UserError("Por favor complete la clave técnica antes de continuar.")
                if self.from_number <= 0 or self.to_number <= 0:
                    raise UserError("Los números de resolución deben ser mayores que cero.")

                required_fields.extend([
                    ('resolution', 'resolución'),
                    ('resolution_date', 'fecha de resolución'),
                    ('technical_key', 'clave técnica'),
                    ('date_from', 'fecha desde'),
                    ('date_to', 'fecha hasta'),
                ])

            for field, field_name in required_fields:
                if not getattr(self, field):
                    raise UserError(f"Por favor complete el campo {field_name} antes de continuar.")



        return True

    def validate_company_data(self):
        company = self.env.company
        required_fields = [
            ('token', 'Token'),
            ('ip_domain', 'IP o Dominio'),
        ]

        for field, field_name in required_fields:
            if not getattr(company, field):
                raise UserError(f"Por favor complete el campo {field_name} de la compañía antes de continuar.")

    def get_payload_resolution(self):
        payload = {
            'type_document_id': self.resolution_type_document_id.id,
            'prefix': self.prefix,
            'from': self.from_number,
            'to': self.to_number,
        }

        if self.resolution_type_document_id.id not in [4, 5, 9, 10]:
            payload.update({
                'resolution': self.resolution,
                'resolution_date': self.resolution_date.strftime('%Y-%m-%d'),
                'technical_key': self.technical_key if self.is_electronic_invoice else '',
                'generated_to_date': self.generate_to_date and self.generate_to_date.strftime('%Y-%m-%d') or 0,
                'date_from': self.date_from.strftime('%Y-%m-%d'),
                'date_to': self.date_to.strftime('%Y-%m-%d'),
            })

        if self.resolution_type_document_id.id in [10, 11, 13, 15]:
            payload.pop('technical_key', None)

        return payload

    def format_url(self, ip_domain, endpoint):
        if not ip_domain.startswith("http"):
            ip_domain = "http://" + ip_domain
        ip_domain = ip_domain.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{ip_domain}/{endpoint}"

    def send_api_resolution(self):
        self.ensure_one()
        self.validate_resolution_data()
        self.validate_company_data()

        company = self.env.company
        payload = self.get_payload_resolution()
        url = self.format_url(company.ip_domain, company.get_endpoint('ConfigResolutionApi'))
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {company.token}',
        }

        try:
            _logger.info("Resolution payload: %s", payload)
            response = requests.put(url, data=json.dumps(payload), headers=headers, timeout=company.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response body: %s", response.text)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('success'):
                self.is_valid_resolution_config = True
                self.api_message_resolution = response_data.get('message', 'Configuración de resolución exitosa')
            else:
                self.is_valid_resolution_config = False
                self.api_message_resolution = response_data.get('message', 'Error en la configuración de resolución')

        except requests.exceptions.RequestException as e:
            raise UserError(f"Error en la solicitud API: {str(e)}")
