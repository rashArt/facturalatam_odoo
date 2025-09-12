from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import requests
import base64
import logging
from urllib.parse import urljoin
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    electronic_invoicing_enabled = fields.Boolean(related='company_id.electronic_invoicing_enabled', readonly=False)
    use_api_mail_server = fields.Boolean(related='company_id.use_api_mail_server', readonly=False)
    type_document_identification_id = fields.Many2one(related='company_id.type_document_identification_id', readonly=False)
    type_organization_id = fields.Many2one(related='company_id.type_organization_id', readonly=False)
    type_regime_id = fields.Many2one(related='company_id.type_regime_id', readonly=False)
    type_liability_id = fields.Many2one(related='company_id.type_liability_id', readonly=False)
    municipality_id = fields.Many2one(related='company_id.municipality_id', readonly=False)
    business_name = fields.Char(related='company_id.business_name', readonly=False)
    merchant_registration = fields.Char(related='company_id.merchant_registration', readonly=False)
    address = fields.Char(related='company_id.address', readonly=False)
    phone = fields.Char(related='company_id.phone', readonly=False)
    email = fields.Char(related='company_id.email', readonly=False)
    mail_host = fields.Char(related='company_id.mail_host', readonly=False)
    mail_port = fields.Char(related='company_id.mail_port', readonly=False)
    mail_username = fields.Char(related='company_id.mail_username', readonly=False)
    mail_password = fields.Char(related='company_id.mail_password', readonly=False)
    mail_encryption = fields.Selection(related='company_id.mail_encryption', readonly=False)
    software_id = fields.Char(related='company_id.software_id', readonly=False)
    software_pin = fields.Integer(related='company_id.software_pin', readonly=False)
    certificate_file = fields.Binary(related='company_id.certificate_file', readonly=False)
    certificate_filename = fields.Char(related='company_id.certificate_filename', readonly=False)
    certificate_password = fields.Char(related='company_id.certificate_password', readonly=False)
    token = fields.Char(related='company_id.token', readonly=False)
    identification_number = fields.Char(related='company_id.identification_number', readonly=False)
    is_valid_company_config = fields.Boolean(related='company_id.is_valid_company_config', readonly=False)
    is_valid_software_config = fields.Boolean(related='company_id.is_valid_software_config', readonly=False)
    is_valid_certificate_config = fields.Boolean(related='company_id.is_valid_certificate_config', readonly=False)
    ip_domain = fields.Char(related='company_id.ip_domain', readonly=False)
    api_timeout = fields.Integer(related='company_id.api_timeout', readonly=False)
    api_message_company = fields.Text(related='company_id.api_message_company', readonly=False)
    api_message_software = fields.Text(related='company_id.api_message_software', readonly=False)
    api_message_certificate = fields.Text(related='company_id.api_message_certificate', readonly=False)
    certificate_expiration_date = fields.Date(related='company_id.certificate_expiration_date', readonly=False)
    environment = fields.Selection(related='company_id.environment', readonly=False)
    environment_message = fields.Text(string="Mensaje de la API para el Entorno Actual")
    numbering_range_message = fields.Text(string="Mensaje de la API para el NumberingRange")
    use_test_id = fields.Boolean(related='company_id.use_test_id', readonly=False)
    test_set_id = fields.Char(related='company_id.test_set_id', readonly=False, store=True)
    payroll_software_id = fields.Char(related='company_id.payroll_software_id', readonly=False)
    payroll_software_pin = fields.Integer(related='company_id.payroll_software_pin', readonly=False)
    payroll_test_set_id = fields.Char(related='company_id.payroll_test_set_id', readonly=False)
    use_payroll_test_id = fields.Boolean(related='company_id.use_payroll_test_id', readonly=False)
    api_message_payroll_software = fields.Text(related='company_id.api_message_payroll_software', readonly=False)
    is_valid_payroll_software_config = fields.Boolean(related='company_id.is_valid_payroll_software_config', readonly=False)
    payroll_environment = fields.Selection(related='company_id.payroll_environment', readonly=False)
    payroll_environment_message = fields.Text(string="Mensaje de la API para el Entorno Actual")
    selected_template_id = fields.Many2one(
        'invoice.template',
        string="Plantilla seleccionada",
        readonly=False,
        related="company_id.selected_template_id"
    )
    selected_template_image_binary = fields.Binary(string="Imagen seleccionada")
    selected_template_message = fields.Text(string="Mensaje de la API para la Plantilla")
    enable_payroll_section = fields.Boolean(
        string="Habilitar Sección de Nómina",
        help="Habilita la sección de configuración de software de nómina."
    )

    @api.onchange('selected_template_id', 'ip_domain')
    def _onchange_selected_template_image_url(self):
        """Genera la URL de la imagen al seleccionar una plantilla"""
        for record in self:
            if record.selected_template_id and record.ip_domain:
                image_url = f"{record.ip_domain}/{record.selected_template_id.image_url}"
                # raise UserError(f"url de imagen {image_url}")
                _logger.error(f"url de imagen {image_url}")
                try:
                    response = requests.get(image_url, timeout=10, verify=False)
                    if response.status_code == 200:
                        record.selected_template_image_binary = base64.b64encode(response.content)
                    else:
                        record.selected_template_image_binary = False
                except requests.RequestException:
                    record.selected_template_image_binary = False

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.environment_message',
            self.environment_message or ''
        )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.payroll_environment_message',
            self.payroll_environment_message or ''
        )

    def set_value_nr(self):
        super(ResConfigSettings, self).set_values()
        formatted_message = json.dumps(self.numbering_range_message, indent=4)
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.numbering_range_message',
            formatted_message or ''
        )

    def set_value_tplt(self):
        super(ResConfigSettings, self).set_values()
        formatted_message = json.dumps(self.selected_template_message, indent=4)
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.selected_template_message',
            formatted_message or ''
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        numbering_range_message = self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.numbering_range_message', default=''
        )
        selected_template_message = self.env['ir.config_parameter'].sudo().get_param(
            'res.config.settings.selected_template_message', default=''
        )
        res.update(
            environment_message=self.env['ir.config_parameter'].sudo().get_param(
                'res.config.settings.environment_message',
                default=''
            ),
            numbering_range_message=numbering_range_message,
            selected_template_message=selected_template_message
        )
        return res

    def ChangeEnvironment(self):
        response_message = self.company_id.ChangeEnvironment()
        self.environment_message = response_message
        self.set_values()

    def ChangePayrollEnvironment(self):
        response_message = self.company_id.ChangePayrollEnvironment()
        self.payroll_environment_message = response_message
        self.set_values()

    def NumberingRange(self):
        response_message = self.company_id.NumberingRange()
        self.numbering_range_message = response_message
        self.set_value_nr()

    def action_configure_company(self):
        self.company_id.send_api_configure_company()

    def action_configure_software(self):
        if not self.software_id:
            raise ValidationError("Complete la información del software ID antes de continuar.")
        if  self.software_pin==0:
            raise ValidationError("El software PIN no puede ser 0.")
        if not self.software_pin:
            raise ValidationError("Complete la información del software PIN antes de continuar.")

        if not self.company_id.is_valid_company_config:
            raise ValidationError("Por favor complete la información de la empresa antes de continuar.")
        if not self.token:
            raise ValidationError("Complete la validacion de compañia antes de continuar.")
        self.company_id.send_api_configure_software()

    def action_configure_payroll_software(self):
        if not self.payroll_software_id:
            raise ValidationError("Complete la información del software ID antes de continuar.")
        if  self.payroll_software_pin==0:
            raise ValidationError("El software PIN no puede ser 0.")
        if not self.payroll_software_pin:
            raise ValidationError("Complete la información del software PIN antes de continuar.")

        if not self.company_id.is_valid_company_config:
            raise ValidationError("Por favor complete la información de la empresa antes de continuar.")
        if not self.token:
            raise ValidationError("Complete la validacion de compañia antes de continuar.")
        self.company_id.send_api_configure_payroll_software()

    def action_configure_certificate(self):
        if not self.certificate_file or not self.certificate_password:
            raise ValidationError("Complete la información del certificado antes de continuar.")
        if not self.company_id.is_valid_company_config:
            raise ValidationError("Por favor complete la información de la empresa antes de continuar.")
        if not self.token:
            raise ValidationError("Complete la validacion de compañia antes de continua.")
        self.company_id.send_api_configure_certificate()

    def action_configure_template(self):
        response_message =  self.company_id.send_api_configure_template()
        self.selected_template_message = response_message
        self.set_value_tplt()
