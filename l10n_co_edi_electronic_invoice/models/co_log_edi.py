from odoo import models, fields

class CoLogEdi(models.Model):
    _name = 'co.log.edi'
    _description = 'Log EDI para Colombia'

    _order = 'create_date desc'

    request_id = fields.Many2one('co.request.edi', string='Request EDI', ondelete='cascade')
    status_code = fields.Integer(string='Código de Estado')
    message = fields.Text(string='Mensaje')
    error_code = fields.Integer(string='Código de Error')
    error_message = fields.Text(string='Mensaje de Error')
    payload = fields.Text(string='Payload')
    response = fields.Text(string='Respuesta')
    create_date = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)
    is_valid = fields.Boolean(string='Es Válido', default=False)