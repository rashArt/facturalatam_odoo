from odoo import models, fields, api
import re
from odoo.exceptions import UserError
import json
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    # Definición de campos
    electronic_invoicing_enabled = fields.Boolean(string="Facturación Electrónica Habilitada", default=False)
    use_api_mail_server = fields.Boolean(string="Usar Servidor de Correo API", default=False)
    type_document_identification_id = fields.Many2one('l10n_co_fl.type_document_identification', string="Tipo de Identificación del Documento")
    type_organization_id = fields.Many2one('l10n_co_fl.type.organization', string="Tipo de Organización")
    type_regime_id = fields.Many2one('l10n_co_fl.type.regime', string="Tipo de Régimen")
    type_liability_id = fields.Many2one('l10n_co_fl.type.liability', string="Tipo de Responsabilidad")
    municipality_id = fields.Many2one('l10n_co_fl.municipality', string="Municipio")
    business_name = fields.Char(string="Nombre Comercial")
    merchant_registration = fields.Char(string="Registro Mercantil")
    address = fields.Char(string="Dirección")
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Correo Electrónico")
    mail_host = fields.Char(string="Servidor de Correo")
    mail_port = fields.Char(string="Puerto de Correo")
    mail_username = fields.Char(string="Usuario de Correo")
    mail_password = fields.Char(string="Contraseña de Correo")
    mail_encryption = fields.Selection([('tls', 'TLS'), ('ssl', 'SSL')], string="Encriptación de Correo", default='tls')
    software_id = fields.Char(string="ID del Software")
    software_pin = fields.Integer(string="PIN del Software")
    certificate_file = fields.Binary(string='Archivo de certificado', required=True)
    certificate_filename = fields.Char(string='Nombre de archivo del certificado')
    certificate_password = fields.Char(string="Contraseña del Certificado")
    token = fields.Char(string="Token")
    ip_domain = fields.Char(string="IP o Dominio")
    identification_number = fields.Char(string="Número de Identificación")
    is_valid_company_config = fields.Boolean(string="Configuración de Empresa Válida")
    api_message_company = fields.Text(string="Mensaje de la API para la Empresa")
    is_valid_software_config = fields.Boolean(string="Configuración de Software Válida")
    api_message_software = fields.Text(string="Mensaje de la API para el Software")
    is_valid_certificate_config = fields.Boolean(string="Configuración de Certificado Válida")
    api_message_certificate = fields.Text(string="Mensaje de la API para el Certificado")
    certificate_expiration_date = fields.Date(string="Fecha de Expiración del Certificado")
    use_test_id = fields.Boolean(string="Entorno de Habilitación", default=False)
    test_set_id = fields.Char(string="Test Set ID", default="no_test_set_id")
    selected_template_id = fields.Many2one('invoice.template', string="Plantilla de Factura")
    payroll_software_id = fields.Char(string="ID del Software de Nómina")
    payroll_software_pin = fields.Integer(string="PIN del Software de Nómina")
    payroll_test_set_id = fields.Char(string="Test Set ID Nomina")
    use_payroll_test_id = fields.Boolean(string="Entorno de Habilitación", default=False)
    is_valid_payroll_software_config = fields.Boolean(string="Configuración de Software de nomina Válida")
    api_message_payroll_software = fields.Text(string="Mensaje de la API para el Software de nomina")
    # Nuevo campo para el entorno
    environment = fields.Selection([
        ('test', 'Pruebas'),
        ('production', 'Producción'),
    ], string="Entorno", default='test')

    payroll_environment = fields.Selection([
        ('test', 'Pruebas'),
        ('production', 'Producción'),
    ], string="Entorno", default='test')

    # Nuevo campo para el tiempo de espera de la API
    api_timeout = fields.Integer(string="Tiempo de Espera de la API (segundos)", default=30)

    def validate_email(self, email):
        email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not email or not email_pattern.match(email):
            raise UserError("Por favor ingrese un correo electrónico válido.")

    def validate_phone(self, phone):
        phone_cleaned = re.sub(r'\D', '', phone)
        phone_pattern = re.compile(r'^\d{7,15}$')
        if not phone_cleaned or not phone_pattern.match(phone_cleaned):
            raise UserError("El número de teléfono debe tener entre 7 y 15 dígitos.")
        return phone_cleaned

    def validate_mandatory_fields(self):
        required_fields = [
            ('business_name', "nombre de la empresa"),
            ('address', "dirección"),
            ('phone', "teléfono"),
            ('email', "correo electrónico"),
            ('merchant_registration', "registro mercantil"),
            ('identification_number', "número de identificación"),
            ('type_document_identification_id', "tipo de identificación"),
            ('type_organization_id', "tipo de organización"),
            ('type_regime_id', "tipo de régimen"),
            ('type_liability_id', "tipo de responsabilidad"),
            ('municipality_id', "municipio"),
            ('ip_domain', "IP o dominio")
        ]

        for field, field_name in required_fields:
            if not getattr(self, field):
                raise UserError(f"Por favor complete {field_name} de la empresa antes de continuar.")

    def validate_mail_server(self):
        if self.use_api_mail_server:
            mail_fields = [
                ('mail_host', "servidor de correo"),
                ('mail_port', "puerto de correo"),
                ('mail_username', "usuario de correo"),
                ('mail_password', "contraseña de correo")
            ]
            for field, field_name in mail_fields:
                if not getattr(self, field):
                    raise UserError(f"Complete la información del {field_name} antes de continuar.")

    def validate_configure_company_json(self):
        self.validate_mail_server()
        self.validate_mandatory_fields()
        self.phone = self.validate_phone(self.phone)
        self.validate_email(self.email)
        return True

    def get_endpoint(self, name):
        data_url = self.env['ir.config_parameter'].search([('key', '=', name)], limit=1)
        if data_url:
            return data_url.value
        raise UserError(f"Endpoint {name} no encontrado.")

    def calculate_dv(self, identification_number):
        factores = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        nit_reversed = str(identification_number)[::-1]
        suma = sum(int(nit_reversed[i]) * factores[i] for i in range(len(nit_reversed)))
        residuo = suma % 11
        return residuo if residuo in [0, 1] else 11 - residuo

    def format_url(self, ip_domain, endpoint):
        if not ip_domain.startswith("http"):
            ip_domain = "http://" + ip_domain
        ip_domain = ip_domain.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{ip_domain}/{endpoint}"

    def get_company_endpoint(self):
        endpoint_default = self.get_endpoint('ConfigCompanyApi')
        dv = self.calculate_dv(self.identification_number)
        formatted_endpoint = f"{endpoint_default}{self.identification_number}/{dv}"
        return self.format_url(self.ip_domain, formatted_endpoint)

    def get_software_endpoint(self):
        return self.format_url(self.ip_domain, self.get_endpoint('ConfigSoftwareApi'))

    def get_payroll_software_endpoint(self):
        return self.format_url(self.ip_domain, self.get_endpoint('ConfigPayrollSoftwareApi'))

    def get_certificate_endpoint(self):
        return self.format_url(self.ip_domain, self.get_endpoint('ConfigCertificateApi'))

    def validate_json_format(self, json_data):
        required_keys = {
            'type_document_identification_id': int,
            'type_organization_id': int,
            'type_regime_id': int,
            'type_liability_id': int,
            'business_name': str,
            'merchant_registration': str,
            'municipality_id': int,
            'address': str,
            'phone': str,
            'email': str
        }

        if self.use_api_mail_server:
            required_keys.update({
                'mail_host': str,
                'mail_port': str,
                'mail_username': str,
                'mail_password': str,
                'mail_encryption': str
            })

        try:
            data = json.loads(json_data)
        except json.JSONDecodeError:
            raise UserError("El JSON proporcionado no es válido.")

        for key, expected_type in required_keys.items():
            if key not in data:
                raise UserError(f"Falta la clave requerida: {key}")
            if not isinstance(data[key], expected_type):
                raise UserError(f"El valor de {key} debe ser de tipo {expected_type.__name__}")

    def get_payload_company(self):
        payload = {
            'type_document_identification_id': self.type_document_identification_id.id,
            'type_organization_id': self.type_organization_id.id,
            'type_regime_id': self.type_regime_id.id,
            'type_liability_id': self.type_liability_id.id,
            'business_name': self.business_name,
            'merchant_registration': self.merchant_registration,
            'municipality_id': self.municipality_id.id,
            'address': self.address,
            'phone': self.phone,
            'email': self.email
        }

        if self.use_api_mail_server:
            payload.update({
                'mail_host': self.mail_host,
                'mail_port': self.mail_port,
                'mail_username': self.mail_username,
                'mail_password': self.mail_password,
                'mail_encryption': self.mail_encryption
            })

        return payload

    def get_payload_software(self):
        payload = {
            'id': str(self.software_id),
            'pin': int(self.software_pin)
        }
        return payload

    def get_payload_payroll_software(self):
        payload = {
            'idpayroll': str(self.payroll_software_id),
            'pinpayroll': int(self.payroll_software_pin)
        }
        return payload

    def get_payload_certificate(self):
        certificate_base64 = self.certificate_file.decode('utf-8') if self.certificate_file else ''
        payload = {
            'certificate': certificate_base64,
            'password': self.certificate_password
        }
        return payload

    def get_header_basic(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def get_header_bearer(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

    def send_api_configure_company(self):
        self.token = False
        self.is_valid_company_config = False
        self.api_message_company = False
        self.validate_configure_company_json()
        endpoint_company = self.get_company_endpoint()
        payload_company = self.get_payload_company()
        payload_json = json.dumps(payload_company, indent=4)
        self.validate_json_format(payload_json)
        header = self.get_header_basic()

        _logger.info("URL: %s", endpoint_company)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)

        try:
            response = requests.post(endpoint_company, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response body: %s", response.text)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")

        response_data = response.json()

        # Asignar los valores del token y los mensajes de la API
        self.token = response_data.get('token')
        self.is_valid_company_config = response_data.get('success', False)
        self.api_message_company = response_data.get('message')

        _logger.info("Respuesta de la API: %s", response_data)
        return response_data

    def send_api_configure_software(self):
        self.is_valid_software_config = False
        self.api_message_software = False
        if not self.token:
            raise UserError("Token no disponible. Configure la empresa primero para obtener un token.")

        endpoint_software = self.get_software_endpoint()
        payload_software = self.get_payload_software()
        payload_json = json.dumps(payload_software, indent=4)
        header = self.get_header_bearer()

        _logger.info("URL: %s", endpoint_software)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)

        try:
            response = requests.put(endpoint_software, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response body: %s", response.text)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")

        response_data = response.json()

        # Asignar los valores del mensaje de la API
        self.is_valid_software_config = response_data.get('success', False)
        self.api_message_software = response_data.get('message')

        _logger.info("Respuesta de la API: %s", response_data)
        return response_data

    def send_api_configure_payroll_software(self):
        self.is_valid_payroll_software_config = False
        self.api_message_payroll_software = False
        if not self.token:
            raise UserError("Token no disponible. Configure la empresa primero para obtener un token.")

        endpoint_payroll_software = self.get_payroll_software_endpoint()
        payload_payroll_software = self.get_payload_payroll_software()
        payload_json = json.dumps(payload_payroll_software, indent=4)
        header = self.get_header_bearer()

        _logger.info("URL: %s", endpoint_payroll_software)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)

        try:
            response = requests.put(endpoint_payroll_software, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response body: %s", response.text)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")

        response_data = response.json()

        # Asignar los valores del mensaje de la API
        self.is_valid_payroll_software_config = response_data.get('success', False)
        self.api_message_payroll_software = response_data.get('message')

        _logger.info("Respuesta de la API: %s", response_data)
        return response_data

    def send_api_configure_certificate(self):
        self.is_valid_certificate_config = False
        self.api_message_certificate = False
        self.certificate_expiration_date = False
        if not self.token:
            raise UserError("Token no disponible. Configure la empresa primero para obtener un token.")

        if not self.certificate_file or not self.certificate_password:
            raise UserError("Por favor, complete el archivo del certificado y la contraseña antes de continuar.")

        endpoint_certificate = self.get_certificate_endpoint()
        payload_certificate = self.get_payload_certificate()
        payload_json = json.dumps(payload_certificate, indent=4)
        header = self.get_header_bearer()

        _logger.info("URL: %s", endpoint_certificate)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)

        try:
            response = requests.put(endpoint_certificate, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            _logger.info("Response body: %s", response.text)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")

        response_data = response.json()

        # Asignar los valores del mensaje de la API y la fecha de expiración del certificado
        self.is_valid_certificate_config = response_data.get('success', False)
        self.api_message_certificate = response_data.get('message')
        expiration_date_str = response_data.get('certificado', {}).get('expiration_date')
        if expiration_date_str:
            self.certificate_expiration_date = datetime.strptime(expiration_date_str, "%Y/%m/%d %H:%M:%S").date()

        _logger.info("Respuesta de la API: %s", response_data)
        return response_data

    def get_environment_endpoint(self):
        return self.format_url(self.ip_domain, self.get_endpoint('ChangeEnvironment'))

    def _get_payload_environment(self, env_type):
        """Genera el payload para cambiar el ambiente."""
        if env_type == 'environment':
            return {'type_environment_id': 1 if self.environment == 'production' else 2}
        elif env_type == 'payroll_environment':
            return {'payroll_type_environment_id': 1 if self.payroll_environment == 'production' else 2}
        return {}

    def _send_environment_request(self, payload):
        """Envía la solicitud HTTP con el payload proporcionado."""
        payload_json = json.dumps(payload, indent=4)
        header = self.get_header_bearer()
        url = self.get_environment_endpoint()

        _logger.info("URL: %s", url)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)

        try:
            response = requests.put(url, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            response.raise_for_status()
            return response.json().get('message')
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")

    def ChangeEnvironment(self):
        """Cambia el entorno general."""
        endpoint = self.get_environment_endpoint()
        payload = self._get_payload_environment('environment')
        return self._send_environment_request(payload)

    def ChangePayrollEnvironment(self):
        """Cambia el entorno de nómina."""
        payload = self._get_payload_environment('payroll_environment')
        return self._send_environment_request(payload)

    def get_numberinrange_endpoint(self):
        return self.format_url(self.ip_domain, self.get_endpoint('NumberingRange'))

    def NumberingRange(self):
        url = self.get_numberinrange_endpoint()
        software_id = self.software_id
        payload = {
            'IDSoftware': software_id
        }
        payload_json = json.dumps(payload, indent=4)
        header = self.get_header_bearer()
        _logger.info("URL: %s", url)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)
        try:
            response = requests.post(url, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
            logging.info(response.json())
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")
        if response.status_code == 200:
            return response.json()

    def send_api_configure_template(self):
        url = self.format_url(self.ip_domain, self.get_endpoint('Templates'))
        template_id = self.selected_template_id.api_template_id
        payload = {
            'id': template_id
        }
        payload_json = json.dumps(payload, indent=4)
        header = self.get_header_bearer()
        _logger.info("URL: %s", url)
        _logger.info("Headers: %s", header)
        _logger.info("Payload: %s", payload_json)
        try:
            response = requests.put(url, headers=header, data=payload_json, timeout=self.api_timeout, verify=False)
            _logger.info("Response status code: %s", response.status_code)
            response.raise_for_status()  # Levanta un error si la respuesta contiene un status code de error
            logging.info(response.json())
        except requests.exceptions.RequestException as e:
            _logger.error("Error al enviar la solicitud: %s", e)
            raise UserError(f"Error al enviar la solicitud: {e}")
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('message')
