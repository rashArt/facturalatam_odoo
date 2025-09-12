from odoo import models, fields

class AccountMoveHealthLine(models.Model):
    _name = 'account.move.health.line'
    _description = 'Línea de Usuarios del Sector Salud'

    move_id = fields.Many2one('account.move', string='Factura', ondelete='cascade')
    health_type_document_identification_id = fields.Selection([
        ('1', 'Cédula de ciudadanía CC'),
        ('2', 'Cédula de extranjería CE'),
        ('3', 'Carné diplomatico CD'),
        ('4', 'Pasaporte PA'),
        ('5', 'Salvoconducto SC'),
        ('6', 'Permiso especial de permanencia PE'),
        ('7', 'Registro civil de nacimiento RC'),
        ('8', 'Tarjeta de identidad TI'),
        ('9', 'Certificado de nacido vivo CN'),
        ('10', 'Adulto sin identificar AS'),
        ('11', 'Menor sin identificar MS'),
        ('12', 'Documento extranjero DE'),
        ('13', 'Sin identificación SI'),
    ], string="Tipo de Documento de Identificación", default='1')
    health_type_user_id = fields.Selection([
        ('1', 'Contributivo cotizante - 01'),
        ('2', 'Contributivo beneficiario - 02'),
        ('3', 'Contributivo adicional - 03'),
        ('4', 'Subsidiado - 04'),
        ('5', 'Sin régimen - 05'),
        ('6', 'Especiales o de Excepción cotizante - 06'),
        ('7', 'Especiales o de Excepción beneficiario - 07'),
        ('8', 'Particular - 08'),
        ('9', 'Tomador/Amparado ARL - 09'),
        ('10', 'Tomador/Amparado SOAT - 10'),
        ('11', 'Tomador/Amparado Planes voluntarios de salud - 11'),
    ], string="Tipo de Usuario del Sector Salud", default='1')
    health_contracting_payment_method_id = fields.Selection([
        ('1', 'Paquete/Canasta/Conjunto Integral en Salud - 01'),
        ('2', 'Grupos Relacionados por Diagnóstico - 02'),
        ('3', 'Integral por grupo de riesgo - 03'),
        ('4', 'Pago por contacto de especialidad - 04'),
        ('5', 'Pago por escenario de atención - 05'),
        ('6', 'Pago por tipo de servicio - 06'),
        ('7', 'Pago global prospectivo por episodio - 07'),
        ('8', 'Pago global prospectivo por grupo de riesgo - 08'),
        ('9', 'Pago global prospectivo por especialidad - 09'),
        ('10', 'Pago global prospectivo por nivel de complejidad - 10'),
        ('11', 'Capacitación - 11'),
        ('12', 'Por servicio - 12'),
    ], string="Metodo de pago del contrato", default='1')
    health_coverage_id = fields.Selection([
        ('1', 'Plan de beneficios en salud financiado con UPC - 01'),
        ('2', 'Presupuesto máximo - 02'),
        ('3', 'Prima EPS/EOC, no asegurados SOAT - 03'),
        ('4', 'Cobertura Póliza SOAT - 04'),
        ('5', 'Cobertura ARL - 05'),
        ('6', 'Cobertura ADRES - 06'),
        ('7', 'Cobertura Salud Pública - 07'),
        ('8', 'Cobertura entidad territorial, recursos de oferta - 08'),
        ('9', 'Urgencias población migrante - 09'),
        ('10', 'Plan complementario en salud - 10'),
        ('11', 'Plan medicina prepagada - 11'),
        ('12', 'Otras pólizas en salud - 12'),
        ('13', 'Cobertura Régimen Especial o Excepción - 13'),
        ('14', 'Cobertura Fondo Nacional de Salud de las Personas Privadas de la Libertad - 14'),
        ('15', 'Particular - 15'),
    ], string="Tipo de cobertura", default='1')
    provider_code = fields.Char(string="Código del proveedor")
    identification_number = fields.Char(string="Número de identificación")
    surname = fields.Char(string="Apellido")
    second_surname = fields.Char(string="Segundo apellido")
    first_name = fields.Char(string="Nombre")
    middle_name = fields.Char(string="Segundo nombre")
    autorization_numbers = fields.Char(string="Números de autorización")
    mipres = fields.Char(string="Mipres")
    mipres_delivery = fields.Char(string="Entrega mipres")
    contract_number = fields.Char(string="Número de contrato")
    policy_number = fields.Char(string="Número de póliza")
    co_payment = fields.Integer(string="Copago", default=0.0)
    moderating_fee = fields.Integer(string="Cuota moderadora", default=0.0)
    recovery_fee = fields.Integer(string="Cuota de recuperacion", default=0.0)
    shared_payment = fields.Integer(string="Pago compartido", default=0.0)